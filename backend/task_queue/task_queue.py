#
# @author GAULT Rudy
# @company Cloud Temple
# @created_at 2025-03-25 13:53:23
# @updated_by GAULT Rudy
# @updated_at 2025-03-25 13:55:41
#
import threading
import queue
import time
from typing import Dict, Any, Callable

class TaskQueue:
    def __init__(self, num_workers: int = 2):
        """
        Initialise une file d'attente avec un nombre spécifique de workers.
        
        Args:
            num_workers: Nombre de threads de travail parallèles
        """
        self.task_queue = queue.Queue()
        self.workers = []
        self.should_stop = threading.Event()
        
        # Démarrer les workers
        for _ in range(num_workers):
            worker = threading.Thread(target=self._worker_loop)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            
    def _worker_loop(self):
        """Boucle principale pour chaque worker"""
        while not self.should_stop.is_set():
            try:
                # Récupérer une tâche avec timeout pour vérifier périodiquement should_stop
                task, callback = self.task_queue.get(timeout=1)
                try:
                    result = task()
                    if callback:
                        callback(result)
                except Exception as e:
                    print(f"Erreur pendant l'exécution de la tâche: {e}")
                finally:
                    # Marquer la tâche comme terminée
                    self.task_queue.task_done()
            except queue.Empty:
                continue
                
    def add_task(self, task: Callable, callback: Callable = None):
        """
        Ajoute une tâche à la file d'attente.
        
        Args:
            task: Fonction à exécuter
            callback: Fonction à appeler avec le résultat de la tâche
        """
        self.task_queue.put((task, callback))
        
    def shutdown(self):
        """Arrête tous les workers et attend leur terminaison"""
        self.should_stop.set()
        for worker in self.workers:
            worker.join()