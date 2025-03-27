#
# @author GAULT Rudy
# @company Cloud Temple
# @created_at 2025-03-25 13:52:00
# @updated_by GAULT Rudy
# @updated_at 2025-03-27 21:35:03
#

import os
import psycopg2
from psycopg2 import pool
import json
from typing import Dict, List, Any, Optional

class Database:
    """Classe pour interagir avec la base de données PostgreSQL"""
    
    def __init__(self):
        """Initialise la connexion à la base de données"""
        db_name = os.environ.get('DB_NAME', 'coursero')
        db_user = os.environ.get('DB_USER', 'coursero')
        db_password = os.environ.get('DB_PASSWORD', 'coursero_secure_password')
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '5432')
        
        # Créer un pool de connexions
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 10,
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
    
    def get_connection(self):
        """Obtient une connexion du pool"""
        return self.connection_pool.getconn()
    
    def release_connection(self, conn):
        """Libère une connexion et la renvoie au pool"""
        self.connection_pool.putconn(conn)
    
    def create_submission(self, user_id: str, course: str, exercise: str, language: str, status: str):
        """
        Crée une nouvelle soumission dans la base de données
        
        Args:
            user_id: ID de l'utilisateur
            course: Identifiant du cours
            exercise: Identifiant de l'exercice
            language: Langage de programmation
            status: Statut de la soumission
        
        Returns:
            ID de la soumission créée
        """
        conn = self.get_connection()
        submission_id = None
        
        try:
            with conn.cursor() as cursor:
                # Obtenir les IDs des entités
                cursor.execute("SELECT course_id FROM courses WHERE course_code = %s", (course,))
                course_result = cursor.fetchone()
                if not course_result:
                    cursor.execute("INSERT INTO courses (course_name, course_code) VALUES (%s, %s) RETURNING course_id", 
                                 (f"Course {course}", course))
                    course_id = cursor.fetchone()[0]
                else:
                    course_id = course_result[0]
                
                # Obtenir ou créer l'exercice
                cursor.execute("SELECT exercise_id FROM exercises WHERE course_id = %s AND exercise_number = %s", 
                             (course_id, exercise.replace('ex', '')))
                exercise_result = cursor.fetchone()
                if not exercise_result:
                    cursor.execute("INSERT INTO exercises (course_id, exercise_name, exercise_number) VALUES (%s, %s, %s) RETURNING exercise_id", 
                                 (course_id, f"Exercise {exercise}", exercise.replace('ex', '')))
                    exercise_id = cursor.fetchone()[0]
                else:
                    exercise_id = exercise_result[0]
                
                # Obtenir l'ID du langage
                cursor.execute("SELECT language_id FROM languages WHERE language_code = %s", (language,))
                language_result = cursor.fetchone()
                if not language_result:
                    cursor.execute("INSERT INTO languages (language_name, language_code) VALUES (%s, %s) RETURNING language_id", 
                                 (language.capitalize(), language))
                    language_id = cursor.fetchone()[0]
                else:
                    language_id = language_result[0]
                
                # Créer la soumission
                cursor.execute("""
                    INSERT INTO submissions (user_id, exercise_id, language_id, status, submit_time)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING submission_id
                """, (user_id, exercise_id, language_id, status))
                
                submission_id = cursor.fetchone()[0]
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            print(f"Erreur lors de la création de la soumission: {e}")
            raise
        finally:
            self.release_connection(conn)
            
        return submission_id
    
    def update_submission(self, user_id: str, course: str, exercise: str, language: str, 
                         score: float, details: Dict, status: str):
        """
        Met à jour une soumission existante
        
        Args:
            user_id: ID de l'utilisateur
            course: Identifiant du cours
            exercise: Identifiant de l'exercice
            language: Langage de programmation
            score: Score obtenu (0-100)
            details: Détails de l'évaluation
            status: Nouveau statut
        """
        conn = self.get_connection()
        
        try:
            with conn.cursor() as cursor:
                # Obtenir l'ID de la soumission la plus récente pour cet utilisateur/cours/exercice/langage
                cursor.execute("""
                    SELECT s.submission_id 
                    FROM submissions s
                    JOIN exercises e ON s.exercise_id = e.exercise_id
                    JOIN courses c ON e.course_id = c.course_id
                    JOIN languages l ON s.language_id = l.language_id
                    WHERE s.user_id = %s AND c.course_code = %s 
                    AND e.exercise_number = %s AND l.language_code = %s
                    ORDER BY s.submit_time DESC
                    LIMIT 1
                """, (user_id, course, exercise.replace('ex', ''), language))
                
                result = cursor.fetchone()
                if not result:
                    print(f"Aucune soumission trouvée pour mettre à jour")
                    return
                
                submission_id = result[0]
                
                # Mettre à jour la soumission
                cursor.execute("""
                    UPDATE submissions 
                    SET status = %s, score = %s, details = %s, completion_time = NOW()
                    WHERE submission_id = %s
                """, (status, score, json.dumps(details), submission_id))
                
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            print(f"Erreur lors de la mise à jour de la soumission: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def get_user_submissions(self, user_id: str) -> List[Dict]:
        """
        Récupère toutes les soumissions d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Liste des soumissions avec leurs détails
        """
        conn = self.get_connection()
        submissions = []
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT s.submission_id, c.course_name, e.exercise_name, 
                           l.language_code, s.status, s.score, s.submit_time
                    FROM submissions s
                    JOIN exercises e ON s.exercise_id = e.exercise_id
                    JOIN courses c ON e.course_id = c.course_id
                    JOIN languages l ON s.language_id = l.language_id
                    WHERE s.user_id = %s
                    ORDER BY s.submit_time DESC
                """, (user_id,))
                
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    submission = dict(zip(columns, row))
                    # Formater les données pour l'API
                    submissions.append({
                        'id': submission['submission_id'],
                        'courseName': submission['course_name'],
                        'exerciseName': submission['exercise_name'],
                        'language': submission['language_code'],
                        'status': submission['status'],
                        'score': submission['score'],
                        'submitTime': submission['submit_time'].isoformat()
                    })
                
        except Exception as e:
            print(f"Erreur lors de la récupération des soumissions: {e}")
            raise
        finally:
            self.release_connection(conn)
            
        return submissions

    def get_available_courses(self) -> List[Dict]:
        """
        Récupère la liste des cours disponibles
        
        Returns:
            Liste des cours avec leurs IDs et noms
        """
        conn = self.get_connection()
        courses = []
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT course_id, course_name, course_code FROM courses")
                
                for row in cursor.fetchall():
                    courses.append({
                        'id': row[2],  # Utiliser le code du cours comme ID pour l'API
                        'name': row[1]
                    })
                
        except Exception as e:
            print(f"Erreur lors de la récupération des cours: {e}")
        finally:
            self.release_connection(conn)
            
        return courses
        
    def get_exercises_for_course(self, course_code: str) -> List[Dict]:
        """
        Récupère la liste des exercices pour un cours spécifique
        
        Args:
            course_code: Code du cours
            
        Returns:
            Liste des exercices disponibles
        """
        conn = self.get_connection()
        exercises = []
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT e.exercise_id, e.exercise_name, e.exercise_number
                    FROM exercises e
                    JOIN courses c ON e.course_id = c.course_id
                    WHERE c.course_code = %s
                    ORDER BY e.exercise_number
                """, (course_code,))
                
                for row in cursor.fetchall():
                    exercises.append({
                        'id': f"ex{row[2]}",  # Format "ex1", "ex2", etc.
                        'number': row[2],
                        'name': row[1]
                    })
                
        except Exception as e:
            print(f"Erreur lors de la récupération des exercices: {e}")
        finally:
            self.release_connection(conn)
            
        return exercises
    
    def close(self):
        """Ferme le pool de connexions"""
        if self.connection_pool:
            self.connection_pool.closeall()

    def user_exists(self, email):
        """Vérifie si un utilisateur avec cet email existe déjà"""
        conn = self.get_connection()
        exists = False
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s", (email,))
                exists = cursor.fetchone()[0] > 0
        except Exception as e:
            print(f"Erreur lors de la vérification de l'existence de l'utilisateur: {e}")
        finally:
            self.release_connection(conn)
            
        return exists

    def create_user(self, user_id, email, password_hash, full_name):
        """Crée un nouvel utilisateur dans la base de données"""
        conn = self.get_connection()
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (id, email, password, full_name) VALUES (%s, %s, %s, %s)",
                    (user_id, email, password_hash, full_name)
                )
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Erreur lors de la création de l'utilisateur: {e}")
            raise
        finally:
            self.release_connection(conn)