"""
Database SQLite per storage dati storici
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class OptionsDatabase:
    """Database per storage dati opzioni e sentiment"""
    
    def __init__(self, db_path: str = "options_data.db"):
        self.db_path = Path(db_path)
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            
            cursor = self.conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS options_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    expiration DATE NOT NULL,
                    timestamp DATETIME NOT NULL,
                    current_price REAL,
                    total_puts INTEGER,
                    total_calls INTEGER,
                    put_volume INTEGER,
                    call_volume INTEGER,
                    put_oi INTEGER,
                    call_oi INTEGER,
                    pcr_volume REAL,
                    pcr_oi REAL,
                    skew_25d REAL,
                    skew_10d REAL,
                    iv_mean REAL,
                    iv_std REAL,
                    data_json TEXT,
                    UNIQUE(ticker, expiration, timestamp)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sentiment_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    sentiment_score REAL,
                    confidence REAL,
                    tickers_mentioned TEXT,
                    published_date DATETIME,
                    fetch_timestamp DATETIME NOT NULL,
                    metadata_json TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT UNIQUE NOT NULL,
                    ticker TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    strength REAL,
                    confidence REAL,
                    reason TEXT,
                    trigger_timestamp DATETIME NOT NULL,
                    expiration_timestamp DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    metadata_json TEXT
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_options_ticker ON options_data(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_options_timestamp ON options_data(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sentiment_timestamp ON sentiment_data(fetch_timestamp)')
            
            self.conn.commit()
            logger.info(f"✅ Database inizializzato: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ Errore inizializzazione database: {e}")
    
    def save_options_data(self, ticker: str, options_data: Dict):
        try:
            from analysis.skew_analyzer import SkewAnalyzer
            from analysis.pcr_analyzer import PCRAnalyzer
            
            current_price = options_data.get('current_price', 0)
            expiration = options_data.get('expiration')
            timestamp = options_data.get('timestamp', datetime.now())
            
            if not expiration:
                logger.warning(f"Nessuna scadenza per {ticker}")
                return
            
            skew_analyzer = SkewAnalyzer()
            pcr_analyzer = PCRAnalyzer()
            
            skew_metrics = skew_analyzer.calculate_skew(options_data)
            pcr_metrics = pcr_analyzer.calculate_pcr(options_data)
            
            cursor = self.conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO options_data (
                    ticker, expiration, timestamp, current_price,
                    total_puts, total_calls, put_volume, call_volume,
                    put_oi, call_oi, pcr_volume, pcr_oi,
                    skew_25d, skew_10d, iv_mean, iv_std, data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ticker,
                expiration,
                timestamp,
                current_price,
                len(options_data.get('puts', [])),
                len(options_data.get('calls', [])),
                pcr_metrics.get('put_volume', 0),
                pcr_metrics.get('call_volume', 0),
                pcr_metrics.get('put_oi', 0),
                pcr_metrics.get('call_oi', 0),
                pcr_metrics.get('pcr_volume', 0),
                pcr_metrics.get('pcr_oi', 0),
                skew_metrics.get('skew_25d', 0),
                skew_metrics.get('skew_10d', 0),
                skew_metrics.get('iv_mean', 0),
                skew_metrics.get('iv_std', 0),
                json.dumps(options_data, default=str)
            ))
            
            self.conn.commit()
            logger.debug(f"✅ Dati opzioni salvati per {ticker} {expiration}")
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio dati opzioni {ticker}: {e}")
    
    def get_historical_skew(self, ticker: str, days: int = 30) -> pd.DataFrame:
        try:
            query = '''
                SELECT 
                    timestamp,
                    skew_25d,
                    skew_10d,
                    current_price,
                    pcr_volume,
                    pcr_oi
                FROM options_data
                WHERE ticker = ?
                AND timestamp >= datetime('now', '-? days')
                ORDER BY timestamp
            '''
            
            df = pd.read_sql_query(query, self.conn, params=(ticker, days))
            
            if df.empty:
                logger.warning(f"Nessun dato storico per {ticker}")
                return pd.DataFrame()
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Errore recupero storico skew {ticker}: {e}")
            return pd.DataFrame()
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("✅ Connessione database chiusa")

if __name__ == "__main__":
    db = OptionsDatabase("test.db")
    print("Database inizializzato con successo")
    db.close()
