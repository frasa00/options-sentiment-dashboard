"""
volatility_analyzer.py - Esteso con analisi volatilità durante ribassi
"""
class VolatilityAnalyzer:
    def __init__(self, vix_data, historical_vol):
        self.vix_data = vix_data
        self.historical_vol = historical_vol
    
    def analyze_volatility_regime(self, market_return):
        """
        Analizza comportamento volatilità durante movimenti di mercato
        
        TUO punto: "Volatilità se mercato scende davvero la volatilità esplode"
        """
        vix_current = self.vix_data.get('current', 0)
        vix_previous = self.vix_data.get('previous', 0)
        vix_change = vix_current - vix_previous
        
        # Analisi regime volatilità
        if market_return < -1.0:  # Ribasso forte > 1%
            if vix_change > 3.0:  # VIX esplode
                regime = "PANIC"
                message = "🔴 VOLATILITÀ ESPLODE: Mercato in forte ribasso (-{:.1%}) e VIX +{:.1f} punti → Paura estrema".format(
                    abs(market_return), vix_change
                )
            elif vix_change > 0:
                regime = "FEAR"
                message = "🟠 Paura in aumento durante ribasso"
            else:
                regime = "DIVERGENCE"
                message = "🟡 Divergenza: Mercato scende ma VIX cala → Attenzione"
        
        elif market_return < -0.5:  # Ribasso moderato
            if vix_change > 2.0:
                regime = "CAUTION"
                message = "🟠 Cautela: Ribasso moderato con VIX in aumento"
            else:
                regime = "NORMAL"
                message = "🟢 Movimento normale"
        
        else:  # Mercato stabile o in rialzo
            if vix_change > 2.0:
                regime = "UNEXPECTED_FEAR"
                message = "🟡 Paura inaspettata in mercato stabile/rialzista"
            else:
                regime = "CALM"
                message = "🟢 Mercato calmo"
        
        return {
            'regime': regime,
            'vix_current': vix_current,
            'vix_change': vix_change,
            'market_return': market_return,
            'message': message,
            'is_volatility_spiking': vix_change > 2.0 and market_return < -0.5
        }
    
    def get_volatility_metrics(self):
        """Metriche complete volatilità"""
        return {
            'vix': self.vix_data.get('current', 0),
            'vix_1d_change': self.vix_data.get('current', 0) - self.vix_data.get('previous', 0),
            'vix_1w_change': self.vix_data.get('current', 0) - self.vix_data.get('week_ago', 0),
            'term_structure': self._analyze_term_structure(),
            'volatility_regime': self._get_regime_classification()
        }
    
    def _analyze_term_structure(self):
        """Analizza struttura temporale volatilità"""
        # Implementa logica per contango/backwardation
        return "Backwardation"  # o "Contango"
    
    def _get_regime_classification(self):
        """Classifica regime volatilità"""
        vix = self.vix_data.get('current', 0)
        
        if vix < 15:
            return "COMPLACENCY"  # Compiacenza
        elif vix < 20:
            return "NORMAL"  # Normale
        elif vix < 25:
            return "CAUTIOUS"  # Cautela
        elif vix < 30:
            return "FEAR"  # Paura
        else:
            return "PANIC"  # Panico
