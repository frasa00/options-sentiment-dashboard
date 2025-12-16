"""
Scheduler per task periodici
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Scheduler per task periodici"""
    
    def __init__(self):
        self.tasks = []
        self.is_running = False
        self.thread = None
    
    def add_task(self, name: str, func: Callable, interval_seconds: int,
                 enabled: bool = True, **kwargs):
        """Aggiungi un task periodico"""
        task = {
            'name': name,
            'function': func,
            'interval': interval_seconds,
            'enabled': enabled,
            'last_run': None,
            'next_run': datetime.now(),
            'kwargs': kwargs
        }
        self.tasks.append(task)
        logger.info(f"Task aggiunto: {name} (ogni {interval_seconds}s)")
    
    def add_daily_task(self, name: str, func: Callable, hour: int, minute: int = 0):
        """Aggiungi un task giornaliero"""
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if next_run < now:
            next_run += timedelta(days=1)
        
        task = {
            'name': name,
            'function': func,
            'type': 'daily',
            'hour': hour,
            'minute': minute,
            'next_run': next_run,
            'enabled': True
        }
        self.tasks.append(task)
        logger.info(f"Task giornaliero aggiunto: {name} alle {hour:02d}:{minute:02d}")
    
    def start(self):
        """Avvia lo scheduler"""
        if self.is_running:
            logger.warning("Scheduler già in esecuzione")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Scheduler avviato")
    
    def stop(self):
        """Ferma lo scheduler"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler fermato")
    
    def _run_scheduler(self):
        """Loop principale dello scheduler"""
        while self.is_running:
            try:
                now = datetime.now()
                
                for task in self.tasks:
                    if not task['enabled']:
                        continue
                    
                    if task['next_run'] <= now:
                        try:
                            logger.debug(f"Esecuzione task: {task['name']}")
                            task['function'](**task.get('kwargs', {}))
                        except Exception as e:
                            logger.error(f"Errore esecuzione task {task['name']}: {e}")
                        
                        # Calcola prossima esecuzione
                        if task.get('type') == 'daily':
                            task['next_run'] += timedelta(days=1)
                        else:
                            task['next_run'] = now + timedelta(seconds=task['interval'])
                        
                        task['last_run'] = now
                
                time.sleep(1)  # Controlla ogni secondo
                
            except Exception as e:
                logger.error(f"Errore nello scheduler: {e}")
                time.sleep(5)
    
    def get_status(self) -> Dict:
        """Ottieni stato dello scheduler"""
        status = {
            'is_running': self.is_running,
            'total_tasks': len(self.tasks),
            'enabled_tasks': sum(1 for t in self.tasks if t['enabled']),
            'tasks': []
        }
        
        for task in self.tasks:
            task_info = {
                'name': task['name'],
                'enabled': task['enabled'],
                'last_run': task['last_run'],
                'next_run': task['next_run']
            }
            status['tasks'].append(task_info)
        
        return status

if __name__ == "__main__":
    scheduler = TaskScheduler()
    print("TaskScheduler pronto per l'uso")
