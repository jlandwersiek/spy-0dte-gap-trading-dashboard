"""Yahoo Finance client with rate limiting"""
import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Dict
from utils.rate_limiter import YahooRateLimiter

# Initialize global rate limiter
yahoo_limiter = YahooRateLimiter()

def safe_yahoo_download(symbol: str, **kwargs):
    """Safe Yahoo Finance download with rate limiting"""
    try:
        yahoo_limiter.wait_if_needed(symbol)
        yahoo_limiter.record_request(symbol)
        
        kwargs['progress'] = False
        return yf.download(symbol, **kwargs)
        
    except Exception as e:
        if "Rate limit" in str(e) or "Too Many Requests" in str(e):
            return pd.DataFrame()
        else:
            raise e

@st.cache_data(ttl=30)
def get_cached_yahoo_data(symbol: str, period: str, interval: str):
    """Cached Yahoo Finance data to reduce API calls"""
    return safe_yahoo_download(symbol, period=period, interval=interval)

class YahooClient:
    """Yahoo Finance client wrapper"""
    
    def __init__(self):
        pass
    
    def get_spy_data(self, period: str = '1d', interval: str = '1m') -> pd.DataFrame:
        """Get SPY data from Yahoo Finance"""
        return get_cached_yahoo_data('SPY', period, interval)
    
    def get_sector_data(self, symbols: list, period: str = '1d', interval: str = '1m') -> Dict:
        """Get sector ETF data from Yahoo Finance"""
        sector_data = {}
        
        for symbol in symbols:
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
            except:
                continue
        
        return sector_data
    
    def get_indices_data(self, indices: list) -> Dict:
        """Get major indices data for internals calculation"""
        index_data = {}
        
        for idx in indices:
            try:
                hist = get_cached_yahoo_data(idx, '1d', '1m')
                if not hist.empty:
                    change_pct = ((hist['Close'].iloc[-1] - hist['Open'].iloc[0]) / hist['Open'].iloc[0]) * 100
                    volume_ratio = hist['Volume'].iloc[-1] / hist['Volume'].mean() if len(hist) > 1 else 1.0
                    index_data[idx] = {'change_pct': change_pct, 'volume_ratio': volume_ratio}
            except:
                continue
        
        return index_data
