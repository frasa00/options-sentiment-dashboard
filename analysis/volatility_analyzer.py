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
            
            if otm_calls.empty or
