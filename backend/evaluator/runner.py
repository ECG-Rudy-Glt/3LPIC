#
# @author GAULT Rudy
# @company Cloud Temple
# @created_at 2025-03-25 13:51:39
# @updated_by GAULT Rudy
# @updated_at 2025-03-27 21:36:33
#
import subprocess
import os
import signal
import tempfile
import resource
from pathlib import Path
from typing import Dict, List, Tuple

from .security import Sandbox

class CodeRunner:
    def __init__(self, timeout: int = 5, max_memory: int = 50 * 1024 * 1024):
        """
        Initialise le runner avec des contraintes de sécurité.
        
        Args:
            timeout: Temps maximum d'exécution en secondes
            max_memory: Mémoire maximale en octets (50MB par défaut)
        """
        self.timeout = timeout
        self.max_memory = max_memory
        self.sandbox = Sandbox()
        
    def run_python_code(self, file_path: str, arguments: List[str]) -> Tuple[str, str, int]:
        """
        Exécute un fichier Python avec les arguments donnés.
        
        Returns:
            Tuple de (stdout, stderr, exit_code)
        """
        # Créer une copie du fichier dans l'environnement sandbox
        sandbox_dir = self.sandbox.create_sandbox_environment("python")
        
        try:
            # Copier le fichier de code vers la sandbox
            target_file = os.path.join(sandbox_dir, "tmp", "code.py")
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            with open(file_path, 'r') as src, open(target_file, 'w') as dst:
                dst.write(src.read())
            
            # Préparation de la commande
            cmd = ["python3", "/tmp/code.py"] + arguments
            
            # Mode sécurisé: utiliser chroot via la classe Sandbox
            if os.geteuid() == 0:  # Si on est root, on peut utiliser chroot
                return self.sandbox.execute_in_sandbox(sandbox_dir, cmd)
            else:
                # Sinon, utiliser la méthode avec les limites de ressources
                return self._execute_with_constraints(cmd)
                
        finally:
            # Nettoyer l'environnement sandbox
            self.sandbox.cleanup(sandbox_dir)
        
    def run_c_code(self, file_path: str, arguments: List[str]) -> Tuple[str, str, int]:
        """
        Compile et exécute un fichier C avec les arguments donnés.
        
        Returns:
            Tuple de (stdout, stderr, exit_code)
        """
        # Créer un fichier temporaire pour l'exécutable
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            executable = tmp.name
            
        try:
            # Compiler le code C
            compile_cmd = ["gcc", file_path, "-o", executable, "-std=c99", "-Wall"]
            compile_result = subprocess.run(
                compile_cmd, 
                capture_output=True, 
                text=True
            )
            
            if compile_result.returncode != 0:
                # Échec de compilation
                return ("", f"Erreur de compilation:\n{compile_result.stderr}", compile_result.returncode)
            
            # Créer l'environnement sandbox
            sandbox_dir = self.sandbox.create_sandbox_environment("c")
            
            try:
                # Copier l'exécutable vers la sandbox
                target_exec = os.path.join(sandbox_dir, "tmp", "code")
                os.makedirs(os.path.dirname(target_exec), exist_ok=True)
                shutil.copy(executable, target_exec)
                os.chmod(target_exec, 0o755)  # Rendre exécutable
                
                # Préparation de la commande
                cmd = ["/tmp/code"] + arguments
                
                # Mode sécurisé: utiliser chroot via la classe Sandbox
                if os.geteuid() == 0:  # Si on est root, on peut utiliser chroot
                    return self.sandbox.execute_in_sandbox(sandbox_dir, cmd)
                else:
                    # Sinon, utiliser la méthode avec les limites de ressources
                    return self._execute_with_constraints(cmd)
                    
            finally:
                # Nettoyer l'environnement sandbox
                self.sandbox.cleanup(sandbox_dir)
            
        finally:
            # Nettoyer l'exécutable temporaire
            if os.path.exists(executable):
                os.remove(executable)
    
    def _execute_with_constraints(self, cmd: List[str]) -> Tuple[str, str, int]:
        """
        Exécute une commande avec des contraintes de ressources.
        
        Args:
            cmd: Liste des éléments de la commande à exécuter
            
        Returns:
            Tuple de (stdout, stderr, exit_code)
        """
        try:
            # Définir la fonction de pré-exécution pour limiter les ressources
            def limit_resources():
                # Limiter la mémoire
                resource.setrlimit(resource.RLIMIT_AS, (self.max_memory, self.max_memory))
                # Empêcher la création de processus enfants
                resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
                # Limiter le temps CPU
                resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))
                
            # Exécuter le programme avec les contraintes
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                preexec_fn=limit_resources
            )
            
            return (process.stdout, process.stderr, process.returncode)
            
        except subprocess.TimeoutExpired:
            return ("", "Délai d'exécution dépassé", -1)
        except Exception as e:
            return ("", f"Erreur lors de l'exécution: {str(e)}", -2)