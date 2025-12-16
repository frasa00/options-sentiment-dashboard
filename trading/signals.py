"""
Generatore segnali trading
"""

from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class SignalGenerator:
    """Generatore di segnali trading"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.recent_signals = []
    
    def generate_signals(self, ticker: str, skew_data: Dict, pcr_data: Dict, 
                        sentiment_data: Dict) -> List[Dict]:
        """Genera segnali basati sui dati"""
        signals = []
        
        try:
            # Segnale da skew
            skew_value = skew_data.get('skew_25d_net', 0)
            if skew_value > 0.02:  # Skew > 2%
                signals.append({
                    'type': 'skew_high',
                    'direction': 'bearish_alert',
                    'strength': min(skew_value * 100, 8),
                    'reason': f'Skew elevato: {skew_value:.3f}',
                    'timestamp': datetime.now()
                })
            
            # Segnale da PCR
            pcr_value = pcr_data.get('pcr_volume', 0)
            if pcr_value > 1.5:  # PCR > 1.5
                signals.append({
                    'type': 'pcr_high',
                    'direction': 'hedge_recommended',
                    'strength': min(pcr_value, 9),
                    'reason': f'PCR elevato: {pcr_value:.2f}',
                    'timestamp': datetime.now()
                })
            
            # Segnale da sentiment
            sentiment_score = sentiment_data.get('final_score', 0)
            if abs(sentiment_score) > 0.5:  |Sentiment| > 0.5
                direction = 'bearish' if sentiment_score < 0 else 'bullish'
                signals.append({
                    'type': 'sentiment_extreme',
                    'direction': f'{direction}_sentiment',
                    'strength': min(abs(sentiment_score) * 10, 7),
                    'reason': f'Sentiment {direction}: {sentiment_score:.2f}',
                    'timestamp': datetime.now()
                })
            
            # Segnale combinato
            if len(signals) >= 2:
                signals.append({
                    'type': 'combined_alert',
                    'direction': 'high_attention',
                    'strength': 8,
                    'reason': f'Multipli segnali attivi ({len(signals)})',
                    'timestamp': datetime.now()
                })
            
            # Aggiungi a storico
            self.recent_signals.extend(signals)
            if len(self.recent_signals) > 50:
                self.recent_signals = self.recent_signals[-50:]
            
            return signals
            
        except Exception as e:
            logger.error(f"Errore generazione segnali: {e}")
            return []
    
    def get_recent_signals(self, ticker: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Ottieni segnali recenti"""
        if ticker:
            filtered = [s for s in self.recent_signals if ticker in str(s)]
        else:
            filtered = self.recent_signals
        
        return filtered[-limit:]
    
    def clear_signals(self):
        """Pulisci storico segnali"""
        self.recent_signals = []

if __name__ == "__main__":
    generator = SignalGenerator()
    print("SignalGenerator pronto per l'uso")
