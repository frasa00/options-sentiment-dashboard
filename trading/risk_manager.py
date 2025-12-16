"""
Gestione rischio base
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    """Manager per gestione rischio base"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'max_position_pct': 0.05,
            'stop_loss_pct': 0.02,
            'max_daily_trades': 5
        }
        self.daily_trades = 0
    
    def analyze_trade_risk(self, ticker: str, position_size: float, 
                          current_price: float) -> Dict:
        """Analizza rischio di un trade"""
        try:
            max_position = self.config['max_position_pct']
            stop_loss = current_price * (1 - self.config['stop_loss_pct'])
            
            risk_amount = position_size * (current_price - stop_loss)
            risk_pct = risk_amount / position_size if position_size > 0 else 0
            
            return {
                'ticker': ticker,
                'position_size': position_size,
                'current_price': current_price,
                'suggested_stop_loss': stop_loss,
                'risk_amount': risk_amount,
                'risk_percentage': risk_pct,
                'max_position_allowed': position_size * max_position,
                'within_limits': risk_pct <= max_position,
                'daily_trades_remaining': self.config['max_daily_trades'] - self.daily_trades
            }
            
        except Exception as e:
            logger.error(f"Errore analisi rischio: {e}")
            return {'error': str(e)}
    
    def register_trade(self):
        """Registra un trade eseguito"""
        self.daily_trades += 1
    
    def reset_daily_counts(self):
        """Resetta contatori giornalieri"""
        self.daily_trades = 0
    
    def get_risk_summary(self) -> Dict:
        """Ottieni summary rischio"""
        return {
            'daily_trades': self.daily_trades,
            'max_daily_trades': self.config['max_daily_trades'],
            'trades_remaining': self.config['max_daily_trades'] - self.daily_trades,
            'position_limit_pct': self.config['max_position_pct'],
            'stop_loss_pct': self.config['stop_loss_pct']
        }

if __name__ == "__main__":
    manager = RiskManager()
    print("RiskManager pronto per l'uso")
