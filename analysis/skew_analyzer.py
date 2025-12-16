"""
skew_analyzer.py - Esteso con le nuove funzionalità richieste
"""
import numpy as np
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SkewAnalyzer:
    def __init__(self, options_data):
        self.options_data = options_data
        
    def calculate_25delta_skew(self):
        """
        Calcola lo skew tra Put e Call 25-delta
        """
        try:
            # Ottieni volatilità 25-delta put e call
            put_25d_iv = self._get_option_iv(delta=0.25, option_type='put')
            call_25d_iv = self._get_option_iv(delta=0.25, option_type='call')
            
            skew = put_25d_iv - call_25d_iv  # Differenza in punti volatilità
            skew_percent = (skew / call_25d_iv) * 100 if call_25d_iv > 0 else 0
            
            return {
                'skew_absolute': skew,
                'skew_percent': skew_percent,
                'put_25d_iv': put_25d_iv,
                'call_25d_iv': call_25d_iv,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Errore calcolo skew: {e}")
            return None
    
    def analyze_skew_trend(self, historical_skew_data):
        """
        Analizza trend skew vs movimento mercato
        """
        if len(historical_skew_data) < 2:
            return {"message": "Dati insufficienti"}
        
        current_skew = historical_skew_data[-1]['skew_percent']
        previous_skew = historical_skew_data[-2]['skew_percent']
        skew_change = current_skew - previous_skew
        
        # Simula dati mercato (dovresti integrarli dal tuo fetcher)
        market_return = -1.5  # Esempio: mercato in ribasso
        
        interpretation = ""
        if skew_change < 0 and market_return < 0:
            interpretation = "🔵 Skew in calo in giornata ribassista → il mercato NON crede a questo calo"
        elif skew_change > 0 and market_return < 0:
            interpretation = "🔴 Skew in aumento in giornata ribassista → paura crescente di ulteriori cali"
        elif skew_change < 0 and market_return > 0:
            interpretation = "🟢 Skew in calo in rialzo → sentiment rialzista solido"
        else:
            interpretation = "🟡 Situazione normale"
        
        return {
            'current_skew': current_skew,
            'skew_change': skew_change,
            'market_return': market_return,
            'interpretation': interpretation,
            'alert_level': 'high' if abs(skew_change) > 5 else 'medium' if abs(skew_change) > 2 else 'low'
        }
    
    def _get_option_iv(self, delta, option_type):
        """
        Estrae IV per un dato delta e tipo di opzione
        """
        # Implementazione semplificata - adatta ai tuoi dati
        options = self.options_data.get(option_type, [])
        for opt in options:
            if abs(opt.get('delta', 0) - delta) < 0.05:  # Tolleranza ±5%
                return opt.get('implied_volatility', 0)
        return 0
    
    def generate_option_walls(self, min_oi_threshold=1000):
        """
        Identifica i muri di opzioni (strike con massimo OI)
        """
        walls = {
            'calls': [],
            'puts': [],
            'spot_price': self.options_data.get('spot_price', 0),
            'max_pain': 0
        }
        
        # Trova strike con massimo OI per call
        calls = self.options_data.get('calls', [])
        if calls:
            max_oi_call = max(calls, key=lambda x: x.get('open_interest', 0))
            if max_oi_call.get('open_interest', 0) > min_oi_threshold:
                distance = ((max_oi_call['strike'] - walls['spot_price']) / walls['spot_price']) * 100
                walls['calls'].append({
                    'strike': max_oi_call['strike'],
                    'open_interest': max_oi_call['open_interest'],
                    'distance_percent': distance,
                    'distance_points': max_oi_call['strike'] - walls['spot_price']
                })
        
        # Trova strike con massimo OI per put
        puts = self.options_data.get('puts', [])
        if puts:
            max_oi_put = max(puts, key=lambda x: x.get('open_interest', 0))
            if max_oi_put.get('open_interest', 0) > min_oi_threshold:
                distance = ((max_oi_put['strike'] - walls['spot_price']) / walls['spot_price']) * 100
                walls['puts'].append({
                    'strike': max_oi_put['strike'],
                    'open_interest': max_oi_put['open_interest'],
                    'distance_percent': distance,
                    'distance_points': max_oi_put['strike'] - walls['spot_price']
                })
        
        # Calcola max pain (semplificato)
        if calls and puts:
            all_strikes = set([c['strike'] for c in calls] + [p['strike'] for p in puts])
            pain_points = []
            for strike in all_strikes:
                pain = sum([c['open_interest'] for c in calls if c['strike'] < strike]) + \
                       sum([p['open_interest'] for p in puts if p['strike'] > strike])
                pain_points.append((strike, pain))
            
            if pain_points:
                walls['max_pain'] = min(pain_points, key=lambda x: x[1])[0]
        
        return walls
