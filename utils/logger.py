"""
Sistema logging configurato
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """Configura logger con formattazione personalizzata"""
    
    # Crea logger
    logger = logging.getLogger(name)
    
    # Evita log duplicati
    if logger.handlers:
        return logger
    
    # Imposta livello
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Formattatore
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler file (opzionale)
    try:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass  # Se fallisce, usiamo solo console
    
    return logger

# Logger di default
logger = setup_logger("options_dashboard")
