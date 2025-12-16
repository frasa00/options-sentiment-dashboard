"""
Modulo per fetching sentiment da siti web e Telegram
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import time
from typing import Dict, List, Optional, Tuple
import json
import feedparser
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

class SentimentFetcher:
    """Fetcher per dati sentiment da varie fonti"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.cache = {}
        self.cache_timeout = 300
        
    def fetch_website_articles(self, url: str, max_articles: int = 10) -> List[Dict]:
        cache_key = f"website_{url}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]
        
        try:
            if url.endswith('.xml') or 'rss' in url.lower() or 'feed' in url.lower():
                articles = self._parse_rss_feed(url, max_articles)
            else:
                articles = self._scrape_website(url, max_articles)
            
            for article in articles:
                article['fetch_timestamp'] = datetime.now().isoformat()
                article['source_url'] = url
                article['source_type'] = 'website'
            
            self.cache[cache_key] = articles
            self._update_cache_timestamp(cache_key)
            
            logger.info(f"✅ Scaricati {len(articles)} articoli da {url}")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Errore fetching da {url}: {e}")
            return []
    
    def _parse_rss_feed(self, feed_url: str, max_articles: int) -> List[Dict]:
        articles = []
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries[:max_articles]:
            article = {
                'title': entry.get('title', ''),
                'summary': entry.get('summary', ''),
                'content': entry.get('content', [{}])[0].get('value', '') if entry.get('content') else '',
                'published': entry.get('published', ''),
                'link': entry.get('link', ''),
                'author': entry.get('author', ''),
                'categories': entry.get('tags', [])
            }
            
            if not article['content'] and article['link']:
                try:
                    full_text = self._extract_article_text(article['link'])
                    article['full_text'] = full_text[:5000]
                except:
                    article['full_text'] = article['summary']
            
            articles.append(article)
        
        return articles
    
    def _scrape_website(self, url: str, max_articles: int) -> List[Dict]:
        articles = []
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            article_elements = soup.find_all(['article', 'div'], class_=re.compile(r'(article|post|news|story)', re.I))
            
            if not article_elements:
                article_elements = soup.find_all(['h1', 'h2', 'h3'])
            
            for element in article_elements[:max_articles]:
                article = self._extract_article_from_element(element, url)
                if article and article.get('title'):
                    articles.append(article)
            
        except Exception as e:
            logger.error(f"Errore scraping {url}: {e}")
        
        return articles
    
    def _extract_article_from_element(self, element, base_url: str) -> Optional[Dict]:
        try:
            title = ''
            if element.name in ['h1', 'h2', 'h3']:
                title = element.get_text(strip=True)
            else:
                title_elem = element.find(['h1', 'h2', 'h3'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            if not title:
                return None
            
            link = ''
            link_elem = element.find('a', href=True)
            if link_elem:
                link = urljoin(base_url, link_elem['href'])
            
            summary = ''
            summary_elem = element.find(['p', 'div'], class_=re.compile(r'(summary|excerpt|desc)', re.I))
            if summary_elem:
                summary = summary_elem.get_text(strip=True)[:500]
            
            date = ''
            date_elem = element.find(['time', 'span'], class_=re.compile(r'(date|time|published)', re.I))
            if date_elem:
                date = date_elem.get_text(strip=True)
            
            return {
                'title': title,
                'summary': summary,
                'link': link,
                'published_date': date,
                'full_text': ''
            }
            
        except Exception as e:
            logger.error(f"Errore estrazione articolo: {e}")
            return None
    
    def _extract_article_text(self, url: str) -> str:
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            content_selectors = ['article', 'main', '.content', '.post-content', '.article-content', '[role="main"]']
            
            content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    break
            
            if not content:
                content = soup
            
            text = content.get_text(separator=' ', strip=True)
            text = ' '.join(text.split())
            
            return text[:10000]
            
        except Exception as e:
            logger.error(f"Errore estrazione testo da {url}: {e}")
            return ""
    
    def fetch_all_sources(self, sources_config: Dict) -> Dict[str, List[Dict]]:
        all_data = {
            'websites': [],
            'telegram': [],
            'rss': []
        }
        
        websites = sources_config.get('websites', [])
        for site in websites:
            try:
                articles = self.fetch_website_articles(site['url'])
                for article in articles:
                    article['source_name'] = site['name']
                    article['priority'] = site.get('priority', 1)
                all_data['websites'].extend(articles)
            except Exception as e:
                logger.error(f"Errore sito {site['name']}: {e}")
        
        telegram_channels = sources_config.get('telegram_channels', [])
        for channel in telegram_channels:
            try:
                messages = self._fetch_telegram_public(channel['username'])
                for msg in messages:
                    msg['source_name'] = channel['name']
                    msg['priority'] = channel.get('priority', 1)
                all_data['telegram'].extend(messages)
            except Exception as e:
                logger.error(f"Errore Telegram {channel['name']}: {e}")
        
        rss_feeds = sources_config.get('rss_feeds', [])
        for feed in rss_feeds:
            try:
                articles = self._parse_rss_feed(feed['url'], max_articles=10)
                for article in articles:
                    article['source_name'] = feed['name']
                    article['priority'] = 2
                all_data['rss'].extend(articles)
            except Exception as e:
                logger.error(f"Errore RSS {feed['name']}: {e}")
        
        return all_data
    
    def _fetch_telegram_public(self, channel_username: str) -> List[Dict]:
        """Fetch base per canali Telegram pubblici - da implementare"""
        logger.warning(f"⚠️ Fetch Telegram per {channel_username} - implementazione base")
        return [
            {
                'message': f"Messaggio di esempio da {channel_username}",
                'timestamp': datetime.now().isoformat(),
                'source': channel_username
            }
        ]
    
    def _is_cached(self, cache_key: str) -> bool:
        if cache_key not in self.cache:
            return False
        if cache_key not in self._cache_timestamps:
            return False
        elapsed = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        return elapsed < self.cache_timeout
    
    def _update_cache_timestamp(self, cache_key: str):
        if not hasattr(self, '_cache_timestamps'):
            self._cache_timestamps = {}
        self._cache_timestamps[cache_key] = datetime.now()

if __name__ == "__main__":
    config = {
        'sentiment_sources': {
            'websites': [
                {'name': 'Reuters', 'url': 'https://www.reuters.com/markets'},
                {'name': 'MarketWatch', 'url': 'https://www.marketwatch.com'}
            ]
        }
    }
    
    fetcher = SentimentFetcher(config=config)
    articles = fetcher.fetch_website_articles("https://www.reuters.com/markets")
    print(f"Articoli trovati: {len(articles)}")
