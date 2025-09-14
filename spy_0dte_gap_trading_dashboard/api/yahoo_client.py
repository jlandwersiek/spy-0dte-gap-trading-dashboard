"""Yahoo Finance client with IMPROVED rate limiting"""
import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Dict
import time
import random

class ImprovedYahooRateLimiter:
    """Enhanced rate limiter for Yahoo Finance"""
    
    def __init__(self):
        self.last_request = {}
        self.min_interval = 3.0  # Increased from 1.5 to 3.0 seconds
        self.request_count = 0
        self.session_start = time.time()
        self.max_requests_per_hour = 50  # Reduced from 100 to 50
        self.backoff_factor = 1.0
    
    def can_make_request(self, symbol: str) -> bool:
        """Check if we can make a request for this symbol"""
        current_time = time.time()
        
        # Check hourly limit
        if self.request_count >= self.max_requests_per_hour:
            if (current_time - self.session_start) < 3600:
                return False
            else:
                self.request_count = 0
                self.session_start = current_time
                self.backoff_factor = 1.0  # Reset backoff
        
        # Check per-symbol limit
        if symbol in self.last_request:
            time_since_last = current_time - self.last_request[symbol]
            required_wait = self.min_interval * self.backoff_factor
            if time_since_last < required_wait:
                return False
        
        return True
    
    def wait_if_needed(self, symbol: str):
        """Wait if needed to respect rate limits with exponential backoff"""
        while not self.can_make_request(symbol):
            wait_time = self.min_interval * self.backoff_factor + random.uniform(0.5, 1.5)
            print(f"Rate limit hit for {symbol}, waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
            self.backoff_factor *= 1.2  # Increase backoff
    
    def record_request(self, symbol: str):
        """Record that we made a request"""
        self.last_request[symbol] = time.time()
        self.request_count += 1
    
    def increase_backoff(self):
        """Increase backoff when rate limit is hit"""
        self.backoff_factor = min(self.backoff_factor * 2, 10.0)
        print(f"Increased backoff factor to {self.backoff_factor:.1f}")

# Initialize global improved rate limiter
yahoo_limiter = ImprovedYahooRateLimiter()

def safe_yahoo_download(symbol: str, **kwargs):
    """IMPROVED safe Yahoo Finance download with better rate limiting"""
    max_retries = 3
    base_delay = 2.0
    
    for attempt in range(max_retries):
        try:
            # Wait for rate limiter
            yahoo_limiter.wait_if_needed(symbol)
            
            # Add random jitter to avoid synchronized requests
            jitter = random.uniform(0.1, 0.5)
            time.sleep(jitter)
            
            # Make the request
            kwargs['progress'] = False
            kwargs['auto_adjust'] = False  # Avoid warnings
            kwargs['prepost'] = False
            kwargs['repair'] = False
            
            result = yf.download(symbol, **kwargs)
            yahoo_limiter.record_request(symbol)
            
            if not result.empty:
                return result
            else:
                print(f"Empty data for {symbol} on attempt {attempt + 1}")
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if "rate limit" in error_msg or "too many requests" in error_msg:
                yahoo_limiter.increase_backoff()
                wait_time = base_delay * (2 ** attempt) + random.uniform(1, 3)
                print(f"Rate limit hit for {symbol}, attempt {attempt + 1}, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                continue
            else:
                print(f"Non-rate-limit error for {symbol}: {e}")
                break
    
    print(f"All attempts failed for {symbol}")
    return pd.DataFrame()

@st.cache_data(ttl=60)  # Increased cache time from 30 to 60 seconds
def get_cached_yahoo_data(symbol: str, period: str, interval: str):
    """Cached Yahoo Finance data with longer TTL"""
    return safe_yahoo_download(symbol, period=period, interval=interval)

def clear_yahoo_cache():
    """Clear Yahoo cache when rate limited"""
    get_cached_yahoo_data.clear()
    print("Cleared Yahoo Finance cache")

class YahooClient:
    """Improved Yahoo Finance client wrapper"""
    
    def __init__(self):
        pass
    
    def get_spy_data(self, period: str = '1d', interval: str = '1m') -> pd.DataFrame:
        """Get SPY data from Yahoo Finance with fallbacks"""
        # Try primary interval first
        try:
            data = get_cached_yahoo_data('SPY', period, interval)
            if not data.empty:
                return data
        except:
            pass
            
        # Try fallback intervals
        fallback_intervals = ['5m', '15m', '1h'] if interval == '1m' else ['1h', '1d']
        
        for fallback_interval in fallback_intervals:
            try:
                print(f"Trying fallback interval {fallback_interval} for SPY")
                data = get_cached_yahoo_data('SPY', period, fallback_interval)
                if not data.empty:
                    return data
            except:
                continue
                
        return pd.DataFrame()
    
    def get_sector_data(self, symbols: list, period: str = '1d', interval: str = '1m') -> Dict:
        """Get sector ETF data with improved error handling"""
        sector_data = {}
        
        # Process symbols in smaller batches to avoid rate limiting
        batch_size = 3
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            
            for symbol in batch:
                try:
                    hist = get_cached_yahoo_data(symbol, period, interval)
                    if not hist.empty:
                        change_pct = ((hist['Close'].iloc[-1] - hist['Open'].iloc[0]) / hist['Open'].iloc[0]) * 100
                        sector_data[symbol] = {
                            'current_price': hist['Close'].iloc[-1],
                            'change_pct': change_pct,
                            'volume': hist['Volume'].iloc[-1],
                            'avg_volume': hist['Volume'].mean(),
                            'source': 'Yahoo'
                        }
                except Exception as e:
                    print(f"Failed to get data for {symbol}: {e}")
                    continue
            
            # Add delay between batches
            if i + batch_size < len(symbols):
                time.sleep(2.0)
        
        return sector_data
    
    def get_indices_data(self, indices: list) -> Dict:
        """Get major indices data for internals calculation"""
        index_data = {}
        
        for idx in indices:
            try:
                hist = get_cached_yahoo_data(idx, '1d', '5m')  # Use 5m instead of 1m
                if not hist.empty:
                    change_pct = ((hist['Close'].iloc[-1] - hist['Open'].iloc[0]) / hist['Open'].iloc[0]) * 100
                    volume_ratio = hist['Volume'].iloc[-1] / hist['Volume'].mean() if len(hist) > 1 else 1.0
                    index_data[idx] = {'change_pct': change_pct, 'volume_ratio': volume_ratio}
                else:
                    print(f"Empty data for index {idx}")
            except Exception as e:
                print(f"Error getting {idx}: {e}")
                continue
        
        return index_data
