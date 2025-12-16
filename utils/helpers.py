"""
Funzioni helper utili
"""

import yaml
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Carica configurazione da file YAML"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Errore caricamento config {config_path}: {e}")
        return {}

def save_config(config: Dict[str, Any], config_path: str = "config.yaml"):
    """Salva configurazione su file YAML"""
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return True
    except Exception as e:
        print(f"❌ Errore salvataggio config: {e}")
        return False

def format_price(price: float) -> str:
    """Formatta prezzo in stringa"""
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    else:
        return f"${price:.4f}"

def format_percentage(value: float) -> str:
    """Formatta percentuale"""
    return f"{value:.2%}"

def get_market_hours() -> Dict[str, bool]:
    """Verifica se siamo in market hours (NYSE)"""
    now = datetime.now()
    
    # NYSE: 9:30-16:00 ET, Lun-Ven
    # Semplificato: controlla solo giorno della settimana
    is_weekday = now.weekday() < 5  # 0-4 = Lun-Ven
    
    # Per ora restituiamo sempre True per testing
    # In produzione, controllerebbe anche l'orario
    return {
        'is_market_open': is_weekday,
        'is_weekday': is_weekday,
        'current_time': now.strftime('%H:%M:%S')
    }

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divisione sicura con default"""
    if denominator == 0:
        return default
    return numerator / denominator
