#
# @author GAULT Rudy
# @company Cloud Temple
# @created_at 2025-03-25 13:51:11
# @updated_by GAULT Rudy
# @updated_at 2025-03-25 13:55:59
#
import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

from evaluator.runner import CodeRunner
from evaluator.comparator import ResultComparator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from task_queue.task_queue import TaskQueue
from db.database import Database

class CourserEvaluator:
    def __init__(self):
        self.runner = CodeRunner()
        self.comparator = ResultComparator()
        self.task_queue = TaskQueue(num_workers=2)
        self.db = Database()
        
        # Charger les tests de référence
        self.test_cases = self._load_test_cases()
        
    def _load_test_cases(self) -> Dict:
        """
        Charge les cas de test depuis les fichiers de configuration.
        
        Returns:
            Dictionnaire avec structure {course: {exercise: {language: [...tests...]}}}
        """
        test_cases = {}
        tests_dir = Path(__file__).parent / "tests"
        
        # Structure: tests/{language}/{course}/{exercise}/test_{num}.json
        for lang_dir in tests_dir.iterdir():
            if not lang_dir.is_dir():
                continue
                
            language = lang_dir.name
            
            for course_dir in lang_dir.iterdir():
                if not course_dir.is_dir():
                    continue
                    
                course = course_dir.name
                
                if course not in test_cases:
                    test_cases[course] = {}
                
                for exercise_dir in course_dir.iterdir():
                    if not exercise_dir.is_dir():
                        continue
                        
                    exercise = exercise_dir.name
                    
                    if exercise not in test_cases[course]:
                        test_cases[course][exercise] = {}
                    
                    if language not in test_cases[course][exercise]:
                        test_cases[course][exercise][language] = []
                    
                    # Charger tous les fichiers de test
                    for test_file in sorted(exercise_dir.glob("test_*.json")):
                        with open(test_file, "r") as f:
                            test_data = json.load(f)
                            test_cases[course][exercise][language].append(test_data)
        
        return test_cases
    
    def submit_code(self, user_id: str, course: str, exercise: str, 
                   language: str, code_file_path: str):
        """
        Soumet un code pour évaluation.
        
        Args:
            user_id: ID de l'utilisateur
            course: Identifiant du cours
            exercise: Identifiant de l'exercice
            language: Langage de programmation ('python' ou 'c')
            code_file_path: Chemin vers le fichier de code soumis
        """
        # Créer une tâche d'évaluation
        def evaluation_task():
            return self._evaluate_submission(user_id, course, exercise, language, code_file_path)
        
        # Fonction de rappel pour mettre à jour la base de données
        def update_db(result):
            score, details = result
            self.db.update_submission(
                user_id=user_id,
                course=course,
                exercise=exercise,
                language=language,
                score=score,
                details=details,
                status="completed"
            )
            # Supprimer le fichier soumis après évaluation
            if os.path.exists(code_file_path):
                os.remove(code_file_path)
        
        # Enregistrer la soumission comme "en attente" dans la base de données
        self.db.create_submission(
            user_id=user_id,
            course=course,
            exercise=exercise,
            language=language,
            status="pending"
        )
        
        # Ajouter la tâche à la file d'attente
        self.task_queue.add_task(evaluation_task, update_db)
    
    def _evaluate_submission(self, user_id: str, course: str, exercise: str, 
                            language: str, code_file_path: str) -> Tuple[float, Dict]:
        """
        Évalue une soumission.
        
        Returns:
            Tuple de (score, détails)
        """
        try:
            # Vérifier que les tests existent pour cette combinaison
            if (course not in self.test_cases or 
                exercise not in self.test_cases[course] or
                language not in self.test_cases[course][exercise]):
                return 0.0, {"error": "Aucun test trouvé pour cette combinaison"}
            
            tests = self.test_cases[course][exercise][language]
            results = []
            test_details = []
            
            for i, test in enumerate(tests):
                args = test.get("args", [])
                expected_output = test.get("expected_output", "")
                
                # Exécuter le code avec les arguments du test
                if language == "python":
                    stdout, stderr, exit_code = self.runner.run_python_code(code_file_path, args)
                elif language == "c":
                    stdout, stderr, exit_code = self.runner.run_c_code(code_file_path, args)
                else:
                    return 0.0, {"error": f"Langage non supporté: {language}"}
                
                # Vérifier si l'exécution a réussi
                if exit_code != 0:
                    test_result = False
                    test_details.append({
                        "test_id": i + 1,
                        "success": False,
                        "error": stderr if stderr else f"Code d'erreur: {exit_code}"
                    })
                else:
                    # Comparer la sortie avec la sortie attendue
                    test_result = self.comparator.compare_outputs(stdout, expected_output)
                    test_details.append({
                        "test_id": i + 1,
                        "success": test_result,
                        "actual_output": stdout,
                        "expected_output": expected_output
                    })
                
                results.append(test_result)
            
            # Calculer le score
            score = self.comparator.evaluate_test_results(results)
            return score, {"tests": test_details}
            
        except Exception as e:
            return 0.0, {"error": f"Erreur lors de l'évaluation: {str(e)}"}