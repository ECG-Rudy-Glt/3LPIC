#
# @author GAULT Rudy
# @company Cloud Temple
# @created_at 2025-03-25 13:51:51
# @updated_by GAULT Rudy
# @updated_at 2025-03-25 13:55:18
#
from typing import Dict, List, Tuple

class ResultComparator:
    def __init__(self):
        pass
        
    def compare_outputs(self, output: str, expected_output: str) -> bool:
        """
        Compare la sortie du programme avec la sortie attendue.
        
        Args:
            output: Sortie réelle du programme
            expected_output: Sortie attendue
            
        Returns:
            True si les sorties correspondent, False sinon
        """
        # Normaliser les fins de ligne et supprimer les espaces en fin de ligne
        normalized_output = '\n'.join(line.rstrip() for line in output.strip().splitlines())
        normalized_expected = '\n'.join(line.rstrip() for line in expected_output.strip().splitlines())
        
        return normalized_output == normalized_expected
        
    def evaluate_test_results(self, results: List[bool]) -> float:
        """
        Calcule le score en pourcentage basé sur les résultats des tests.
        
        Args:
            results: Liste de booléens représentant les résultats de chaque test
            
        Returns:
            Pourcentage de tests réussis (0-100)
        """
        if not results:
            return 0.0
            
        successful_tests = sum(1 for result in results if result)
        return (successful_tests / len(results)) * 100.0