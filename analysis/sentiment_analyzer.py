"""
Analisi sentiment da testi
"""

import re
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Analizzatore sentiment per testi finanziari"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        try:
            nltk.data.find('sentiment/vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon', quiet=True)
        
        self.vader = SentimentIntensityAnalyzer()
        self.ticker_pattern = re.compile(r'\b[A-Z]{1,5}\b')
        
        self.bullish_words = {'buy', 'bull', 'bullish', 'long', 'positive', 'gain'}
        self.bearish_words = {'sell', 'bear', 'bearish', 'short', 'negative', 'loss'}
    
    def analyze_text(self, text: str) -> Dict:
        if not text or not isinstance(text, str):
            return self._get_empty_sentiment()
        
        try:
            cleaned_text = self._clean_text(text)
            
            if not cleaned_text:
                return self._get_empty_sentiment()
            
            vader_scores = self.vader.polarity_scores(cleaned_text)
            keyword_scores = self._analyze_keywords(cleaned_text)
            
            final_score = self._combine_scores(
                vader_scores['compound'],
                keyword_scores['net_score']
            )
            
            category = self._categorize_sentiment(final_score)
            tickers = self.extract_tickers(text)
            
            return {
                'text': text[:200],
                'vader_compound': vader_scores['compound'],
                'keyword_net': keyword_scores['net_score'],
                'final_score': final_score,
                'category': category,
                'tickers_mentioned': tickers,
                'word_count': len(cleaned_text.split()),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ Errore analisi sentiment: {e}")
            return self._get_empty_sentiment()
    
    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        text = re.sub(r'@\w+|#\w+', '', text)
        text = re.sub(r'[^\w\s.,!?]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _analyze_keywords(self, text: str) -> Dict:
        words = set(text.lower().split())
        bullish_found = words.intersection(self.bullish_words)
        bearish_found = words.intersection(self.bearish_words)
        net_score = len(bullish_found) - len(bearish_found)
        
        return {
            'bullish_count': len(bullish_found),
            'bearish_count': len(bearish_found),
            'net_score': net_score
        }
    
    def _combine_scores(self, vader_score: float, keyword_score: float) -> float:
        combined = vader_score * 0.7 + (keyword_score / 5) * 0.3
        return max(min(combined, 1), -1)
    
    def _categorize_sentiment(self, score: float) -> str:
        if score >= 0.7:
            return "extremely_bullish"
        elif score >= 0.3:
            return "bullish"
        elif score >= 0.1:
            return "slightly_bullish"
        elif score <= -0.7:
            return "extremely_bearish"
        elif score <= -0.3:
            return "bearish"
        elif score <= -0.1:
            return "slightly_bearish"
        else:
            return "neutral"
    
    def extract_tickers(self, text: str) -> List[str]:
        if not text:
            return []
        tickers_found = self.ticker_pattern.findall(text.upper())
        common_words = {'THE', 'AND', 'FOR', 'YOU', 'ARE'}
        valid_tickers = [t for t in tickers_found if t not in common_words and len(t) >= 2]
        
        seen = set()
        unique_tickers = []
        for t in valid_tickers:
            if t not in seen:
                seen.add(t)
                unique_tickers.append(t)
        
        return unique_tickers
    
    def _get_empty_sentiment(self) -> Dict:
        return {
            'text': '',
            'vader_compound': 0,
            'keyword_net': 0,
            'final_score': 0,
            'category': 'neutral',
            'tickers_mentioned': [],
            'word_count': 0,
            'timestamp': datetime.now(),
            'error': True
        }

if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    test_text = "AAPL stock is looking very strong! Great earnings report."
    result = analyzer.analyze_text(test_text)
    print(f"Test sentiment: {result}")
