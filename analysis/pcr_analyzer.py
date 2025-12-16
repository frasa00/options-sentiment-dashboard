"""
pcr_analyzer.py - Esteso con analisi OI e fragilità sistemica
"""
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PCRAnalyzer:
    def __init__(self, volume_data, oi_data):
        self.volume_data = volume_data
        self.oi_data = oi_data
    
    def calculate_all_pcr(self):
        """
        Calcola tutti i PCR richiesti
        """
        results = {
            'volume': self._calculate_pcr_volume(),
            'open_interest': self._calculate_pcr_oi(),
            'trend': self._analyze_pcr_trend(),
            'systemic_fragility': self._check_systemic_fragility()
        }
        return results
    
    def _calculate_pcr_volume(self):
        """PCR su volume"""
        total_put_volume = sum(self.volume_data.get('puts', {}).values())
        total_call_volume = sum(self.volume_data.get('calls', {}).values())
        
        if total_call_volume > 0:
            pcr = total_put_volume / total_call_volume
        else:
            pcr = 0
        
        interpretation = ""
        if pcr < 1:
            interpretation = "PCR < 1 → Si comprano più call che put (sentiment rialzista)"
        elif pcr > 1.5:
            interpretation = "PCR > 1.5 → Forte hedging o paura (sentiment ribassista)"
        else:
            interpretation = "PCR neutrale"
        
        return {
            'value': round(pcr, 2),
            'interpretation': interpretation,
            'put_volume': total_put_volume,
            'call_volume': total_call_volume
        }
    
    def _calculate_pcr_oi(self):
        """PCR su Open Interest"""
        total_put_oi = sum(self.oi_data.get('puts', {}).values())
        total_call_oi = sum(self.oi_data.get('calls', {}).values())
        
        if total_call_oi > 0:
            pcr_oi = total_put_oi / total_call_oi
        else:
            pcr_oi = 0
        
        # Analisi fragilità sistemica (TUO punto critico)
        fragility_alert = False
        fragility_message = ""
        
        if pcr_oi < 0.9:
            fragility_alert = True
            fragility_message = "⚠️ ALLERTA FRAGILITÀ: PCR OI < 0.9 → poca protezione complessiva nel sistema"
        elif pcr_oi < 1.0:
            fragility_message = "Attenzione: PCR OI < 1 → hedging limitato"
        else:
            fragility_message = "PCR OI > 1 → hedging diffuso presente"
        
        return {
            'value': round(pcr_oi, 2),
            'fragility_alert': fragility_alert,
            'fragility_message': fragility_message,
            'put_oi': total_put_oi,
            'call_oi': total_call_oi,
            'total_oi': total_put_oi + total_call_oi
        }
    
    def _analyze_pcr_trend(self):
        """Analizza trend PCR (semplificato - da integrare con storico)"""
        # Implementa confronto con giorni precedenti
        return {
            'volume_trend': 'increasing',  # 'increasing', 'decreasing', 'stable'
            'oi_trend': 'stable',
            'recommendation': 'Monitorare PCR OI per fragilità sistemica'
        }
    
    def _check_systemic_fragility(self):
        """Controllo avanzato fragilità sistemica"""
        pcr_oi = self._calculate_pcr_oi()['value']
        
        conditions = {
            'pcr_oi_below_0_9': pcr_oi < 0.9,
            'skew_high': False,  # Da integrare con skew analyzer
            'vix_spiking': False,  # Da integrare con volatility analyzer
            'market_decline': False  # Da integrare con dati di mercato
        }
        
        # Se tutte le condizioni sono vere → allerta massima
        if all(conditions.values()):
            return {
                'alert_level': 'CRITICAL',
                'message': '🚨 ALLERTA MASSIMA: Condizioni di fragilità sistemica confermate',
                'actions': [
                    'Ridurre esposizione',
                    'Aumentare hedging',
                    'Monitorare liquidità'
                ]
            }
        elif conditions['pcr_oi_below_0_9']:
            return {
                'alert_level': 'HIGH',
                'message': '⚠️ PCR OI < 0.9 → Fragilità sistemica potenziale',
                'actions': ['Verificare coperture esistenti']
            }
        else:
            return {
                'alert_level': 'LOW',
                'message': 'Nessuna fragilità sistemica rilevata',
                'actions': []
            }
