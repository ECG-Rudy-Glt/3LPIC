#
# @author GAULT Rudy
# @company Cloud Temple
# @created_at 2025-03-25 13:52:00
# @updated_by GAULT Rudy
# @updated_at 2025-03-27 21:42:59
#

import os
import json
import tempfile
import subprocess
from typing import Dict, List, Tuple, Any

from .runner import CodeRunner

class Evaluator:
    """
    Classe pour évaluer le code soumis
    """
    
    def __init__(self, exercises_dir: str = None):
        """
        Initialise l'évaluateur de code
        
        Args:
            exercises_dir: Chemin vers le répertoire contenant les exercices
        """
        self.exercises_dir = exercises_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'exercises'
        )
        self.runner = CodeRunner()
        
    def load_exercise(self, course_id: str, exercise_id: str) -> Dict:
        """
        Charge la définition d'un exercice depuis le fichier JSON
        
        Args:
            course_id: Identifiant du cours
            exercise_id: Identifiant de l'exercice
            
        Returns:
            Dictionnaire contenant la définition de l'exercice
        """
        exercise_path = os.path.join(self.exercises_dir, course_id, f"{exercise_id}.json")
        
        if not os.path.exists(exercise_path):
            raise FileNotFoundError(f"Exercice non trouvé: {exercise_path}")
        
        with open(exercise_path, 'r') as f:
            return json.load(f)
    
    def evaluate_submission(self, file_path: str, course_id: str, exercise_id: str, language: str) -> Dict:
        """
        Évalue une soumission
        
        Args:
            file_path: Chemin vers le fichier soumis
            course_id: Identifiant du cours
            exercise_id: Identifiant de l'exercice
            language: Langage de programmation
            
        Returns:
            Résultats de l'évaluation
        """
        # Charger la définition de l'exercice
        try:
            exercise = self.load_exercise(course_id, exercise_id)
        except FileNotFoundError as e:
            return {
                'status': 'error',
                'message': str(e),
                'score': 0,
                'details': []
            }
        
        # Vérifier que le langage correspond
        if exercise['language'] != language:
            return {
                'status': 'error',
                'message': f"Langage incorrect. Attendu: {exercise['language']}, reçu: {language}",
                'score': 0,
                'details': []
            }
        
        # Exécuter les tests
        results = []
        total_score = 0
        max_score = 0
        
        for test_case in exercise['testCases']:
            # Préparation des arguments d'entrée
            input_args = [str(arg) for arg in test_case['input']]
            expected_output = test_case['expected_output'].strip()
            max_score += test_case['score']
            
            # Exécuter le code
            stdout, stderr, exit_code = self._run_code(file_path, language, input_args)
            actual_output = stdout.strip()
            
            # Vérifier si la sortie correspond à l'attendu
            success = actual_output == expected_output
            score = test_case['score'] if success else 0
            total_score += score
            
            results.append({
                'input': test_case['input'],
                'expected_output': expected_output,
                'actual_output': actual_output,
                'success': success,
                'score': score,
                'error': stderr if stderr else None
            })
        
        # Calculer le score final (sur 100)
        final_score = (total_score / max_score * 100) if max_score > 0 else 0
        
        return {
            'status': 'completed',
            'message': 'Évaluation terminée',
            'score': final_score,
            'details': results
        }
    
    def _run_code(self, file_path: str, language: str, input_args: List[str]) -> Tuple[str, str, int]:
        """
        Exécute le code soumis
        
        Args:
            file_path: Chemin vers le fichier à exécuter
            language: Langage de programmation
            input_args: Arguments d'entrée
            
        Returns:
            Tuple de (stdout, stderr, exit_code)
        """
        if language == 'python':
            return self.runner.run_python_code(file_path, input_args)
        elif language == 'c':
            return self.runner.run_c_code(file_path, input_args)
        else:
            return ('', f"Langage non supporté: {language}", -1)