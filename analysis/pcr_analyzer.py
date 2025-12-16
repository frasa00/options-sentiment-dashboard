"""
Analizzatore Put/Call Ratio
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PCRAnalyzer:
    """Analizzatore per Put/Call Ratio"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.pcr_alert_threshold = self.config.get('pcr_alert_threshold', 1.5)
    
    def calculate_pcr(self, options_data: Dict) -> Dict:
        try:
            calls = options_data.get('calls', pd.DataFrame())
            puts = options_data.get('puts', pd.DataFrame())
            
            if calls.empty or puts.empty:
                return self._get_empty_pcr_metrics()
            
            call_volume = self._calculate_total_volume(calls)
            put_volume = self._calculate_total_volume(puts)
            call_oi = self._calculate_total_oi(calls)
            put_oi = self._calculate_total_oi(puts)
            
            pcr_volume = put_volume / call_volume if call_volume > 0 else 0
            pcr_oi = put_oi / call_oi if call_oi > 0 else 0
            
            return {
                'put_volume': put_volume,
                'call_volume': call_volume,
                'put_oi': put_oi,
                'call_oi': call_oi,
                'pcr_volume': pcr_volume,
                'pcr_oi': pcr_oi,
                'timestamp': datetime.now(),
                'current_price': options_data.get('current_price', 0),
                'above_alert': pcr_volume > self.pcr_alert_threshold
            }
            
        except Exception as e:
            logger.error(f"❌ Errore calcolo PCR: {e}")
            return self._get_empty_pcr_metrics()
    
    def _calculate_total_volume(self, options_df: pd.DataFrame) -> float:
        if 'volume' in options_df.columns:
            return options_df['volume'].sum()
        elif 'lastTradeVolume' in options_df.columns:
            return options_df['lastTradeVolume'].sum()
        else:
            return len(options_df) * 100
    
    def _calculate_total_oi(self, options_df: pd.DataFrame) -> float:
        if 'openInterest' in options_df.columns:
            return options_df['openInterest'].sum()
        else:
            return len(options_df) * 50
    
    def _get_empty_pcr_metrics(self) -> Dict:
        return {
            'put_volume': 0,
            'call_volume': 0,
            'put_oi': 0,
            'call_oi': 0,
            'pcr_volume': 0,
            'pcr_oi': 0,
            'timestamp': datetime.now(),
            'current_price': 0,
            'above_alert': False,
            'error': True
        }

if __name__ == "__main__":
    analyzer = PCRAnalyzer()
    print("PCRAnalyzer pronto per l'uso")
