#!/usr/bin/env python3
"""
PUNTO DI INGRESSO PRINCIPALE - Opzioni & Sentiment Dashboard
"""

import sys
import warnings
from pathlib import Path

# Configura percorsi
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

# Ignora warning non critici
warnings.filterwarnings('ignore')

# Import nostri moduli
from utils.logger import setup_logger
from utils.scheduler import TaskScheduler
from utils.helpers import load_config
from data.database import OptionsDatabase

# Configura logger
logger = setup_logger("main")

class OptionsSentimentApp:
    """Applicazione principale"""
    
    def __init__(self):
        logger.info("🚀 Avvio Opzioni & Sentiment Dashboard")
        
        # Carica configurazione
        self.config = load_config()
        
        # Inizializza componenti
        self.db = OptionsDatabase()
        self.scheduler = TaskScheduler()
        
        # Stato
        self.is_running = False
    
    def setup(self):
        """Setup iniziale"""
        try:
            # Crea directory necessarie
            directories = ['data/historical', 'data/cache', 'logs', 'reports']
            for dir_path in directories:
                full_path = PROJECT_ROOT / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
            
            # Verifica dipendenze
            self._check_dependencies()
            
            logger.info("✅ Setup completato")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore durante il setup: {e}")
            return False
    
    def _check_dependencies(self):
        """Verifica dipendenze base"""
        required = ['pandas', 'numpy', 'yfinance', 'streamlit']
        
        for package in required:
            try:
                __import__(package)
                logger.debug(f"✅ {package} installato")
            except ImportError:
                logger.warning(f"⚠️ {package} non installato")
    
    def start_dashboard(self):
        """Avvia dashboard Streamlit"""
        import subprocess
        import webbrowser
        
        logger.info("🌐 Avvio dashboard Streamlit...")
        
        try:
            # Comando per avviare Streamlit
            cmd = [
                'streamlit', 'run',
                str(PROJECT_ROOT / 'dashboard' / 'app.py'),
                '--server.port', '8501',
                '--theme.base', 'dark'
            ]
            
            # Avvia in subprocess
            process = subprocess.Popen(cmd)
            
            # Attendi e apri browser
            import time
            time.sleep(3)
            webbrowser.open('http://localhost:8501')
            
            logger.info("✅ Dashboard avviato su http://localhost:8501")
            
            # Mantieni processo attivo
            process.wait()
            
        except Exception as e:
            logger.error(f"❌ Errore nell'avvio del dashboard: {e}")
    
    def run(self):
        """Esegui l'applicazione"""
        if not self.setup():
            logger.error("Impossibile avviare l'applicazione")
            return
        
        # Avvia dashboard
        self.start_dashboard()

def main():
    """Funzione principale"""
    app = OptionsSentimentApp()
    app.run()

if __name__ == "__main__":
    main()
