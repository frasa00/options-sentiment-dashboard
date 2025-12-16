"""
Analizzatore volatilità
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class VolatilityAnalyzer:
    """Analizzatore per volatilità"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def calculate_volatility_metrics(self, options_data: Dict) -> Dict:
        try:
            all_options = options_data.get('all_options', pd.DataFrame())
            current_price = options_data.get('current_price', 0)
            
            if all_options.empty or 'iv' not in all_options.columns:
                return self._get_empty_vol_metrics()
            
            iv_series = all_options['iv'].dropna()
            
            if iv_series.empty:
                return self._get_empty_vol_metrics()
            
            vix_index = self._calculate_vix_index(all_options, current_price)
            
            return {
                'iv_mean': float(iv_series.mean()),
                'iv_std': float(iv_series.std()),
                'iv_min': float(iv_series.min()),
                'iv_max': float(iv_series.max()),
                'vix_index': vix_index,
                'timestamp': datetime.now(),
                'current_price': current_price,
                'num_options': len(all_options)
            }
            
        except Exception as e:
            logger.error(f"❌ Errore calcolo volatilità: {e}")
            return self._get_empty_vol_metrics()
    
    def _calculate_vix_index(self, options_df: pd.DataFrame, spot_price: float) -> float:
        try:
            otm_calls = options_df[(options_df['optionType'] == 'call') & 
                                  (options_df['strike'] > spot_price)]
            otm_puts = options_df[(options_df['optionType'] == 'put') & 
                                 (options_df['strike'] < spot_price)]
            
            if otm_calls.empty or otm_puts.empty or 'iv' not in options_df.columns:
                return 20.0
            
            otm_options = pd.concat([otm_calls, otm_puts])
            weights = 1 / (abs(otm_options['strike'] / spot_price - 1) ** 2 + 0.01)
            weights = weights / weights.sum()
            
            vix_value = (otm_options['iv'] * weights).sum() * 100
            vix_value = max(5, min(vix_value, 100))
            
            return float(vix_value)
        except:
            return 20.0
    
    def _get_empty_vol_metrics(self) -> Dict:
        return {
            'iv_mean': 0.2,
            'iv_std': 0.05,
            'iv_min': 0.15,
            'iv_max': 0.25,
            'vix_index': 20.0,
            'timestamp': datetime.now(),
            'current_price': 0,
            'num_options': 0,
            'error': True
        }

if __name__ == "__main__":
    analyzer = VolatilityAnalyzer()
    print("VolatilityAnalyzer pronto per l'uso")
