"""
Modulo per il fetching dei dati opzioni da Yahoo Finance
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Optional, Tuple
import time
import yfinance as yf

warnings.filterwarnings('ignore')

class OptionsFetcher:
    """Fetcher per dati opzioni da Yahoo Finance"""
    
    def __init__(self, source: str = "yfinance", cache_timeout: int = 300):
        self.source = source
        self.cache_timeout = cache_timeout
        self.cache = {}
        self.last_fetch = {}
        self.default_tickers = ["SPY", "QQQ", "IWM", "AAPL", "MSFT"]
        
    def fetch_options_chain(self, ticker: str, expiration: Optional[str] = None) -> Dict:
        cache_key = f"{ticker}_{expiration}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            current_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
            
            if expiration:
                exp_date = expiration
            else:
                exp_dates = stock.options
                if not exp_dates:
                    raise ValueError(f"Nessuna scadenza disponibile per {ticker}")
                exp_date = exp_dates[0]
            
            opt_chain = stock.option_chain(exp_date)
            
            calls = opt_chain.calls.copy()
            calls['optionType'] = 'call'
            calls['moneyness'] = calls['strike'] / current_price
            calls['midPrice'] = (calls['bid'] + calls['ask']) / 2
            
            puts = opt_chain.puts.copy()
            puts['optionType'] = 'put'
            puts['moneyness'] = puts['strike'] / current_price
            puts['midPrice'] = (puts['bid'] + puts['ask']) / 2
            
            all_options = pd.concat([calls, puts], ignore_index=True)
            all_options = self._calculate_greeks(all_options, current_price, exp_date)
            
            data = {
                'current_price': current_price,
                'expiration': exp_date,
                'calls': calls,
                'puts': puts,
                'all_options': all_options,
                'expirations': stock.options,
                'timestamp': datetime.now()
            }
            
            data['metadata'] = {
                'ticker': ticker,
                'fetch_time': datetime.now().isoformat(),
                'source': self.source,
                'expiration': expiration
            }
            
            self.cache[cache_key] = data
            self.last_fetch[cache_key] = datetime.now()
            
            return data
            
        except Exception as e:
            print(f"❌ Errore fetching opzioni per {ticker}: {e}")
            return self._get_empty_options_data(ticker)
    
    def _calculate_greeks(self, options_df: pd.DataFrame, spot: float, expiration: str) -> pd.DataFrame:
        from datetime import datetime
        
        exp_date = datetime.strptime(expiration, '%Y-%m-%d')
        days_to_expiry = (exp_date - datetime.now()).days
        if days_to_expiry <= 0:
            days_to_expiry = 1
        
        risk_free_rate = 0.04
        
        options_df = options_df.copy()
        
        def approx_delta(row):
            moneyness = row['moneyness']
            if row['optionType'] == 'call':
                return min(max(0.5 + (1 - moneyness) * 10, 0), 1)
            else:
                return min(max(0.5 - (1 - moneyness) * 10, -1), 0)
        
        options_df['delta'] = options_df.apply(approx_delta, axis=1)
        options_df['gamma'] = options_df.apply(
            lambda row: 0.1 * np.exp(-((row['moneyness'] - 1) ** 2) / 0.02), axis=1
        )
        options_df['theta'] = -options_df['midPrice'] * 0.01 / np.sqrt(days_to_expiry)
        options_df['vega'] = options_df['midPrice'] * 0.1
        
        return options_df
    
    def _is_cached(self, cache_key: str) -> bool:
        if cache_key not in self.cache:
            return False
        if cache_key not in self.last_fetch:
            return False
        elapsed = (datetime.now() - self.last_fetch[cache_key]).total_seconds()
        return elapsed < self.cache_timeout
    
    def _get_empty_options_data(self, ticker: str) -> Dict:
        return {
            'current_price': 0,
            'expiration': None,
            'calls': pd.DataFrame(),
            'puts': pd.DataFrame(),
            'all_options': pd.DataFrame(),
            'expirations': [],
            'timestamp': datetime.now(),
            'error': True
        }
    
    def get_multiple_chains(self, tickers: List[str]) -> Dict[str, Dict]:
        results = {}
        for ticker in tickers:
            try:
                results[ticker] = self.fetch_options_chain(ticker)
                time.sleep(0.5)
            except Exception as e:
                print(f"Errore per {ticker}: {e}")
                results[ticker] = self._get_empty_options_data(ticker)
        return results
    
    def get_historical_volatility(self, ticker: str, days: int = 30) -> float:
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days * 2)
            
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                return 0.0
            
            hist['returns'] = np.log(hist['Close'] / hist['Close'].shift(1))
            volatility = hist['returns'].std() * np.sqrt(252)
            
            return volatility
            
        except Exception as e:
            print(f"Errore calcolo volatilità per {ticker}: {e}")
            return 0.0

if __name__ == "__main__":
    fetcher = OptionsFetcher(source="yfinance")
    spy_data = fetcher.fetch_options_chain("SPY")
    print(f"Prezzo SPY: {spy_data['current_price']}")
    print(f"Scadenze disponibili: {len(spy_data['expirations'])}")
