"""Tradier API client"""
import requests
from typing import Dict, Optional, Tuple

class TradierAPI:
    """Enhanced Tradier API client - PRIMARY data source"""
    
    def __init__(self, token: str, sandbox: bool = False):
        self.token = token
        self.base_url = "https://sandbox.tradier.com/v1" if sandbox else "https://api.tradier.com/v1"
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test API connection and return status"""
        try:
            response = requests.get(
                f"{self.base_url}/user/profile",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "✅ Connected to Tradier API"
            elif response.status_code == 401:
                return False, "❌ Invalid API token"
            else:
                return False, f"❌ API Error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "❌ Connection timeout"
        except Exception as e:
            return False, f"❌ Connection error: {str(e)}"
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get real-time quote for single symbol"""
        try:
            response = requests.get(
                f"{self.base_url}/markets/quotes",
                params={'symbols': symbol},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                quotes = data.get('quotes', {})
                if 'quote' in quotes:
                    return quotes['quote']
                return {}
            else:
                return None
                
        except Exception as e:
            return None
    
    def get_quotes_bulk(self, symbols: str) -> Optional[Dict]:
        """Get real-time quotes for multiple symbols (comma-separated)"""
        try:
            response = requests.get(
                f"{self.base_url}/markets/quotes",
                params={'symbols': symbols},
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                quotes = data.get('quotes', {})
                if 'quote' in quotes:
                    quote_data = quotes['quote']
                    if isinstance(quote_data, list):
                        return {q['symbol']: q for q in quote_data}
                    else:
                        return {quote_data['symbol']: quote_data}
                return {}
            else:
                return None
                
        except Exception as e:
            return None
    
    def get_historical_quotes(self, symbol: str, interval: str = '1min', 
                            start: str = None, end: str = None) -> Optional[Dict]:
        """Get historical data from Tradier"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval
            }
            if start:
                params['start'] = start
            if end:
                params['end'] = end
            
            response = requests.get(
                f"{self.base_url}/markets/history",
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            return None
    
    def get_options_chain(self, symbol: str, expiration: str) -> Optional[Dict]:
        """Get options chain for symbol and expiration"""
        try:
            response = requests.get(
                f"{self.base_url}/markets/options/chains",
                params={
                    'symbol': symbol,
                    'expiration': expiration,
                    'greeks': 'true'
                },
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            return None
