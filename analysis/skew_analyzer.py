"""
Analisi skew delle opzioni - Core del trading
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SkewAnalyzer:
    """Analizzatore per skew delle opzioni"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.delta_points = self.config.get('delta_points', [0.25, 0.10])
        self.smoothing_window = self.config.get('smoothing_window', 5)
    
    def calculate_skew(self, options_data: Dict) -> Dict:
        try:
            all_options = options_data.get('all_options', pd.DataFrame())
            current_price = options_data.get('current_price', 0)
            
            if all_options.empty or current_price == 0:
                return self._get_empty_skew_metrics()
            
            calls = all_options[all_options['optionType'] == 'call'].copy()
            puts = all_options[all_options['optionType'] == 'put'].copy()
            
            if calls.empty or puts.empty:
                return self._get_empty_skew_metrics()
            
            calls['iv'] = self._calculate_implied_volatility(calls, current_price)
            puts['iv'] = self._calculate_implied_volatility(puts, current_price)
            
            skew_metrics = {}
            
            for delta_target in self.delta_points:
                call_skew = self._calculate_delta_skew(calls, delta_target, current_price, 'call')
                put_skew = self._calculate_delta_skew(puts, delta_target, current_price, 'put')
                skew_net = put_skew - call_skew if put_skew and call_skew else 0
                
                skew_metrics[f'skew_{int(delta_target*100)}d_call'] = call_skew
                skew_metrics[f'skew_{int(delta_target*100)}d_put'] = put_skew
                skew_metrics[f'skew_{int(delta_target*100)}d_net'] = skew_net
            
            skew_index = self._calculate_skew_index(calls, puts, current_price)
            skew_metrics['skew_index'] = skew_index
            
            return {
                **skew_metrics,
                'timestamp': datetime.now(),
                'current_price': current_price,
                'expiration': options_data.get('expiration'),
                'num_calls': len(calls),
                'num_puts': len(puts)
            }
            
        except Exception as e:
            logger.error(f"❌ Errore calcolo skew: {e}")
            return self._get_empty_skew_metrics()
    
    def _calculate_implied_volatility(self, options_df: pd.DataFrame, spot_price: float) -> pd.Series:
        iv_series = []
        for _, row in options_df.iterrows():
            moneyness = row['strike'] / spot_price
            mid_price = row.get('midPrice', (row.get('bid', 0) + row.get('ask', 0)) / 2)
            
            if mid_price <= 0:
                iv = 0.2
            else:
                iv = mid_price / (spot_price * 0.15)
                if moneyness > 1:
                    iv *= (1 + 0.5 * (moneyness - 1))
                else:
                    iv *= (1 - 0.3 * (1 - moneyness))
                iv = max(0.05, min(iv, 1.0))
            
            iv_series.append(iv)
        return pd.Series(iv_series, index=options_df.index)
    
    def _calculate_delta_skew(self, options_df: pd.DataFrame, delta_target: float,
                             spot_price: float, option_type: str) -> Optional[float]:
        if options_df.empty:
            return None
        
        if option_type == 'call':
            otm_options = options_df[options_df['strike'] > spot_price]
        else:
            otm_options = options_df[options_df['strike'] < spot_price]
        
        if otm_options.empty or 'iv' not in otm_options.columns:
            return None
        
        otm_options = otm_options.sort_values('strike')
        strikes = otm_options['strike'].values
        ivs = otm_options['iv'].values
        
        if len(strikes) < 2:
            return None
        
        try:
            from scipy import interpolate
            f = interpolate.interp1d(strikes, ivs, kind='linear', fill_value='extrapolate')
            
            if option_type == 'call':
                target_strike = spot_price * (1 + delta_target)
            else:
                target_strike = spot_price * (1 - delta_target)
            
            target_iv = f(target_strike)
            atm_iv = f(spot_price)
            skew = target_iv - atm_iv
            
            return float(skew)
        except:
            return None
    
    def _calculate_skew_index(self, calls_df: pd.DataFrame, puts_df: pd.DataFrame,
                            spot_price: float) -> float:
        try:
            otm_calls = calls_df[calls_df['strike'] > spot_price]
            otm_puts = puts_df[puts_df['strike'] < spot_price]
            
            if otm_calls.empty or otm_puts.empty:
                return 100.0
            
            def weighted_iv(df):
                if 'iv' not in df.columns or df.empty:
                    return 0.2
                weights = np.abs(df['strike'] - spot_price) / spot_price
                weights = weights / weights.sum()
                return (df['iv'] * weights).sum()
            
            iv_calls = weighted_iv(otm_calls)
            iv_puts = weighted_iv(otm_puts)
            
            skew_ratio = iv_puts / iv_calls if iv_calls > 0 else 1.0
            skew_index = 100 + 100 * np.log(skew_ratio)
            skew_index = max(80, min(skew_index, 180))
            
            return float(skew_index)
        except:
            return 100.0
    
    def _get_empty_skew_metrics(self) -> Dict:
        return {
            'skew_25d_call': 0,
            'skew_25d_put': 0,
            'skew_25d_net': 0,
            'skew_10d_call': 0,
            'skew_10d_put': 0,
            'skew_10d_net': 0,
            'skew_index': 100,
            'timestamp': datetime.now(),
            'current_price': 0,
            'expiration': None,
            'num_calls': 0,
            'num_puts': 0,
            'error': True
        }

if __name__ == "__main__":
    analyzer = SkewAnalyzer()
    print("SkewAnalyzer pronto per l'uso")
