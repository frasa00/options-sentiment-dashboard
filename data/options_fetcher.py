"""
options_fetcher.py - Fetch dati opzioni da Yahoo Finance
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from utils.logger import setup_logger
import time

logger = setup_logger(__name__)

class OptionsFetcher:
    def __init__(self, ticker="SPY", api_key=None):
        self.ticker = ticker
        self.api_key = api_key
        self.ticker_obj = yf.Ticker(ticker)
        
    def fetch_options_data(self, expiration_date=None):
        """
        Fetch dati opzioni con struttura necessaria per gli analizzatori
        """
        try:
            logger.info(f"Fetching options data for {self.ticker}")
            
            # Ottieni dati spot
            spot_data = self.ticker_obj.history(period="1d")
            spot_price = spot_data['Close'].iloc[-1] if not spot_data.empty else 0
            
            # Ottieni date di scadenza disponibili
            if expiration_date is None:
                expirations = self.ticker_obj.options
                if not expirations:
                    raise ValueError(f"Nessuna scadenza disponibile per {self.ticker}")
                expiration_date = expirations[0]  # Prendi la prima scadenza
            
            logger.info(f"Usando scadenza: {expiration_date}")
            
            # Ottieni catena opzioni
            try:
                opt_chain = self.ticker_obj.option_chain(expiration_date)
            except Exception as e:
                logger.error(f"Errore fetch opzioni: {e}")
                # Fallback a dati mock per sviluppo
                return self._get_mock_data(spot_price)
            
            # Processa calls
            calls = []
            if not opt_chain.calls.empty:
                for _, row in opt_chain.calls.iterrows():
                    call = {
                        'strike': row['strike'],
                        'lastPrice': row['lastPrice'],
                        'bid': row['bid'],
                        'ask': row['ask'],
                        'volume': row['volume'],
                        'open_interest': row['openInterest'],
                        'implied_volatility': row['impliedVolatility'],
                        'contractSymbol': row['contractSymbol'],
                        'delta': self._estimate_delta(row, 'call', spot_price),
                        'option_type': 'call'
                    }
                    calls.append(call)
            
            # Processa puts
            puts = []
            if not opt_chain.puts.empty:
                for _, row in opt_chain.puts.iterrows():
                    put = {
                        'strike': row['strike'],
                        'lastPrice': row['lastPrice'],
                        'bid': row['bid'],
                        'ask': row['ask'],
                        'volume': row['volume'],
                        'open_interest': row['openInterest'],
                        'implied_volatility': row['impliedVolatility'],
                        'contractSymbol': row['contractSymbol'],
                        'delta': self._estimate_delta(row, 'put', spot_price),
                        'option_type': 'put'
                    }
                    puts.append(put)
            
            # Calcola metriche aggregati per volume e OI
            volume_data = {
                'calls': {c['strike']: c['volume'] for c in calls if c['volume'] > 0},
                'puts': {p['strike']: p['volume'] for p in puts if p['volume'] > 0}
            }
            
            oi_data = {
                'calls': {c['strike']: c['open_interest'] for c in calls if c['open_interest'] > 0},
                'puts': {p['strike']: p['open_interest'] for p in puts if p['open_interest'] > 0}
            }
            
            # Ottieni dati VIX (per SPY) o volatilità equivalente
            vix_data = self._fetch_vix_data()
            
            # Ottieni performance mercato
            market_return = self._calculate_market_return()
            
            return {
                'spot_price': spot_price,
                'expiration': expiration_date,
                'calls': calls,
                'puts': puts,
                'volume_data': volume_data,
                'oi_data': oi_data,
                'vix_data': vix_data,
                'market_return': market_return,
                'timestamp': datetime.now().isoformat(),
                'ticker': self.ticker
            }
            
        except Exception as e:
            logger.error(f"Errore in fetch_options_data: {e}")
            # Return mock data in caso di errore
            return self._get_mock_data(100)
    
    def _estimate_delta(self, option_row, option_type, spot_price):
        """Stima delta usando Black-Scholes semplificato"""
        try:
            # Questa è una stima semplificata - in produzione usa una libreria proper
            strike = option_row['strike']
            iv = option_row['impliedVolatility']
            time_to_expiry = 30 / 365  # Approssimazione 30 giorni
            
            if spot_price == 0 or iv == 0:
                return 0.5 if option_type == 'call' else -0.5
            
            # Approssimazione molto semplificata del delta
            if option_type == 'call':
                if strike < spot_price:
                    return 0.6 + (spot_price - strike) / spot_price * 0.3
                else:
                    return 0.4 - (strike - spot_price) / spot_price * 0.3
            else:  # put
                if strike < spot_price:
                    return -0.4 + (spot_price - strike) / spot_price * 0.3
                else:
                    return -0.6 - (strike - spot_price) / spot_price * 0.3
                    
        except:
            return 0.5 if option_type == 'call' else -0.5
    
    def _fetch_vix_data(self):
        """Fetch dati VIX"""
        try:
            if self.ticker == "SPY":
                vix = yf.Ticker("^VIX")
                vix_history = vix.history(period="5d")
                
                if not vix_history.empty:
                    current = vix_history['Close'].iloc[-1]
                    previous = vix_history['Close'].iloc[-2] if len(vix_history) > 1 else current
                    week_ago = vix_history['Close'].iloc[0] if len(vix_history) > 4 else current
                    
                    return {
                        'current': float(current),
                        'previous': float(previous),
                        'week_ago': float(week_ago),
                        'change': float(current - previous)
                    }
        except Exception as e:
            logger.warning(f"Errore fetch VIX: {e}")
        
        # Fallback values
        return {
            'current': 18.5,
            'previous': 17.2,
            'week_ago': 16.8,
            'change': 1.3
        }
    
    def _calculate_market_return(self):
        """Calcola ritorno di mercato giornaliero"""
        try:
            hist = self.ticker_obj.history(period="5d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2]
                return ((current / previous) - 1) * 100
        except:
            pass
        return 0.0
    
    def _get_mock_data(self, spot_price=100):
        """Dati mock per sviluppo/testing"""
        logger.info("Usando dati mock per sviluppo")
        
        calls = []
        puts = []
        
        # Genera dati mock per calls
        for i in range(5):
            strike = spot_price * (0.95 + i * 0.025)
            calls.append({
                'strike': strike,
                'lastPrice': max(0.1, (strike - spot_price) * 0.5),
                'bid': max(0.1, (strike - spot_price) * 0.45),
                'ask': max(0.1, (strike - spot_price) * 0.55),
                'volume': 1000 + i * 500,
                'open_interest': 5000 + i * 1000,
                'implied_volatility': 0.2 + i * 0.02,
                'delta': 0.5 - i * 0.1,
                'option_type': 'call'
            })
        
        # Genera dati mock per puts
        for i in range(5):
            strike = spot_price * (0.95 + i * 0.025)
            puts.append({
                'strike': strike,
                'lastPrice': max(0.1, (spot_price - strike) * 0.5),
                'bid': max(0.1, (spot_price - strike) * 0.45),
                'ask': max(0.1, (spot_price - strike) * 0.55),
                'volume': 1200 + i * 600,
                'open_interest': 6000 + i * 1200,
                'implied_volatility': 0.25 + i * 0.03,
                'delta': -0.5 + i * 0.1,
                'option_type': 'put'
            })
        
        volume_data = {
            'calls': {c['strike']: c['volume'] for c in calls},
            'puts': {p['strike']: p['volume'] for p in puts}
        }
        
        oi_data = {
            'calls': {c['strike']: c['open_interest'] for c in calls},
            'puts': {p['strike']: p['open_interest'] for p in puts}
        }
        
        return {
            'spot_price': spot_price,
            'expiration': '2024-01-19',
            'calls': calls,
            'puts': puts,
            'volume_data': volume_data,
            'oi_data': oi_data,
            'vix_data': {
                'current': 18.5,
                'previous': 17.2,
                'week_ago': 16.8,
                'change': 1.3
            },
            'market_return': -1.5,  # Mock: mercato in ribasso del 1.5%
            'timestamp': datetime.now().isoformat(),
            'ticker': self.ticker
        }

# Funzione helper per uso rapido
def fetch_options_snapshot(ticker="SPY", expiration=None):
    """Funzione rapida per fetch dati opzioni"""
    fetcher = OptionsFetcher(ticker)
    return fetcher.fetch_options_data(expiration)
