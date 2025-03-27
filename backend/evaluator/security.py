#
# @author GAULT Rudy
# @company Cloud Temple
# @created_at 2025-03-25 13:52:00
# @updated_by GAULT Rudy
# @updated_at 2025-03-27 21:31:22
#

import os
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

class Sandbox:
    """
    Classe pour exécuter du code dans un environnement isolé et sécurisé
    """
    
    def __init__(self, base_dir: str = None):
        """
        Initialise l'environnement de sandbox
        
        Args:
            base_dir: Répertoire de base pour créer les environnements chroot
        """
        self.base_dir = base_dir or tempfile.mkdtemp(prefix="coursero_sandbox_")
        
    def create_sandbox_environment(self, language: str) -> str:
        """
        Crée un environnement isolé pour exécuter du code
        
        Args:
            language: Langage de programmation à supporter
            
        Returns:
            Chemin vers l'environnement créé
        """
        sandbox_dir = tempfile.mkdtemp(dir=self.base_dir)
        
        # Créer les répertoires nécessaires dans l'environnement chroot
        os.makedirs(os.path.join(sandbox_dir, "bin"), exist_ok=True)
        os.makedirs(os.path.join(sandbox_dir, "lib"), exist_ok=True)
        os.makedirs(os.path.join(sandbox_dir, "lib64"), exist_ok=True)
        os.makedirs(os.path.join(sandbox_dir, "usr", "bin"), exist_ok=True)
        os.makedirs(os.path.join(sandbox_dir, "usr", "lib"), exist_ok=True)
        os.makedirs(os.path.join(sandbox_dir, "tmp"), exist_ok=True)
        
        # Copier les exécutables et bibliothèques nécessaires
        if language == "python":
            self._copy_python_environment(sandbox_dir)
        elif language == "c":
            self._copy_c_environment(sandbox_dir)
            
        return sandbox_dir
        
    def _copy_python_environment(self, sandbox_dir: str):
        """Copie l'interpréteur Python et les bibliothèques nécessaires"""
        # Copier l'interpréteur Python
        shutil.copy("/usr/bin/python3", os.path.join(sandbox_dir, "usr/bin/"))
        
        # Copier les bibliothèques nécessaires (simplifié - en production il faudrait être plus précis)
        python_libs = subprocess.check_output(
            ["ldd", "/usr/bin/python3"], 
            text=True
        ).splitlines()
        
        for lib in python_libs:
            if "=>" in lib and "not found" not in lib:
                lib_path = lib.split("=>")[1].strip().split(" ")[0]
                if lib_path and os.path.exists(lib_path):
                    dest_dir = os.path.join(sandbox_dir, os.path.dirname(lib_path)[1:])
                    os.makedirs(dest_dir, exist_ok=True)
                    shutil.copy(lib_path, dest_dir)
    
    def _copy_c_environment(self, sandbox_dir: str):
        """Copie le compilateur GCC et les bibliothèques nécessaires"""
        # Copier GCC
        shutil.copy("/usr/bin/gcc", os.path.join(sandbox_dir, "usr/bin/"))
        
        # Copier les bibliothèques standard C
        libc_paths = ["/lib/libc.so.6", "/lib64/libc.so.6"]
        for lib_path in libc_paths:
            if os.path.exists(lib_path):
                dest_dir = os.path.join(sandbox_dir, os.path.dirname(lib_path)[1:])
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy(lib_path, dest_dir)
    
    def execute_in_sandbox(self, sandbox_dir: str, cmd: List[str]) -> Tuple[str, str, int]:
        """
        Exécute une commande dans l'environnement isolé
        
        Args:
            sandbox_dir: Chemin vers l'environnement sandbox
            cmd: Commande à exécuter
            
        Returns:
            Tuple de (stdout, stderr, exit_code)
        """
        # Préparer les arguments pour chroot
        chroot_cmd = ["chroot", sandbox_dir] + cmd
        
        try:
            # Exécuter la commande dans l'environnement chroot
            process = subprocess.run(
                chroot_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5  # Timeout de 5 secondes
            )
            
            return (process.stdout, process.stderr, process.returncode)
            
        except subprocess.TimeoutExpired:
            return ("", "Délai d'exécution dépassé", -1)
        except Exception as e:
            return ("", f"Erreur lors de l'exécution: {str(e)}", -2)
            
    def cleanup(self, sandbox_dir: str = None):
        """Nettoie les ressources utilisées par la sandbox"""
        if sandbox_dir and os.path.exists(sandbox_dir):
            shutil.rmtree(sandbox_dir)
            
        if self.base_dir and os.path.exists(self.base_dir) and sandbox_dir != self.base_dir:
            shutil.rmtree(self.base_dir)
