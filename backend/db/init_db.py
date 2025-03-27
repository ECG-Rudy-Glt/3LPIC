#!/usr/bin/env python3
#
# @author GAULT Rudy
# @company Cloud Temple
# @created_at 2025-03-27 22:45:00
#
# Script d'initialisation de la base de données pour Coursero

import os
import psycopg2
import sys

def init_database():
    """Initialise la base de données avec les tables nécessaires"""
    # Récupérer les informations de connexion depuis les variables d'environnement
    db_name = os.environ.get('DB_NAME', 'coursero')
    db_user = os.environ.get('DB_USER', 'coursero')
    db_password = os.environ.get('DB_PASSWORD', 'coursero_secure_password')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '5432')
    
    conn = None
    try:
        # Connexion à la base de données
        print(f"Connexion à la base de données {db_name}...")
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        
        # Créer un curseur
        cur = conn.cursor()
        
        print("Création des tables...")
        
        # Création de la table des utilisateurs
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(36) PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Création de la table des cours
        cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id SERIAL PRIMARY KEY,
            course_name VARCHAR(255) NOT NULL,
            course_code VARCHAR(50) UNIQUE NOT NULL
        )
        """)
        
        # Création de la table des exercices
        cur.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            exercise_id SERIAL PRIMARY KEY,
            course_id INTEGER REFERENCES courses(course_id),
            exercise_name VARCHAR(255) NOT NULL,
            exercise_number INTEGER NOT NULL
        )
        """)
        
        # Création de la table des langages
        cur.execute("""
        CREATE TABLE IF NOT EXISTS languages (
            language_id SERIAL PRIMARY KEY,
            language_name VARCHAR(50) NOT NULL,
            language_code VARCHAR(20) UNIQUE NOT NULL
        )
        """)
        
        # Création de la table des soumissions
        cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            submission_id SERIAL PRIMARY KEY,
            user_id VARCHAR(36) REFERENCES users(id),
            exercise_id INTEGER REFERENCES exercises(exercise_id),
            language_id INTEGER REFERENCES languages(language_id),
            status VARCHAR(20) NOT NULL,
            score FLOAT,
            details JSONB,
            submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_time TIMESTAMP
        )
        """)
        
        # Insertion de données initiales (langages supportés)
        cur.execute("""
        INSERT INTO languages (language_name, language_code)
        VALUES 
            ('Python', 'python'),
            ('C', 'c')
        ON CONFLICT (language_code) DO NOTHING
        """)
        
        # Insertion de données initiales (cours d'exemple)
        cur.execute("""
        INSERT INTO courses (course_name, course_code)
        VALUES 
            ('Algorithmes et structures de données', 'course1'),
            ('Programmation système', 'course2')
        ON CONFLICT (course_code) DO NOTHING
        """)
        
        # Récupérer les IDs des cours insérés
        cur.execute("SELECT course_id, course_code FROM courses WHERE course_code IN ('course1', 'course2')")
        course_ids = {code: id for id, code in cur.fetchall()}
        
        # Insertion d'exercices d'exemple pour chaque cours
        if 'course1' in course_ids:
            course1_id = course_ids['course1']
            cur.execute("""
            INSERT INTO exercises (course_id, exercise_name, exercise_number)
            VALUES 
                (%s, 'Tri à bulle', 1),
                (%s, 'Liste chaînée', 2),
                (%s, 'Arbre binaire', 3)
            ON CONFLICT DO NOTHING
            """, (course1_id, course1_id, course1_id))
        
        if 'course2' in course_ids:
            course2_id = course_ids['course2']
            cur.execute("""
            INSERT INTO exercises (course_id, exercise_name, exercise_number)
            VALUES 
                (%s, 'Gestion de processus', 1),
                (%s, 'Threads', 2),
                (%s, 'Sockets', 3)
            ON CONFLICT DO NOTHING
            """, (course2_id, course2_id, course2_id))
        
        # Valider les changements
        conn.commit()
        
        print("Initialisation terminée avec succès !")
        return True
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Erreur lors de l'initialisation de la base de données: {error}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
