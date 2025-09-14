# analyzers/premium_analyzer.py - FIXED None handling

import requests
import pandas as pd
from datetime import datetime, time, timedelta
import numpy as np
import time as time_module

class PremiumAnalyzer:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://api.tradier.com/v1"
        
    def get_option_chain(self, symbol="SPY", expiration_date=None):
        """Get current option chain for SPY - with better error handling"""
        if not expiration_date:
            expiration_date = datetime.now().strftime("%Y-%m-%d")
            
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Accept': 'application/json'
        }
        
        url = f"{self.base_url}/markets/options/chains"
        params = {
            'symbol': symbol,
            'expiration': expiration_date,
            'greeks': 'true'
        }
        
        try:
            print(f"DEBUG: Requesting options chain for {symbol} on {expiration_date}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            print(f"DEBUG: Options response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"DEBUG: Options response keys: {list(data.keys()) if data else 'None'}")
                return data
            else:
                print(f"DEBUG: Options request failed: {response.status_code} - {response.text[:200]}")
                return None
        except Exception as e:
            print(f"Error fetching option chain: {e}")
            return None

    def get_stock_quote(self, symbol):
        """Get current stock quote"""
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Accept': 'application/json'
        }
        
        url = f"{self.base_url}/markets/quotes"
        params = {'symbols': symbol}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'quotes' in data and 'quote' in data['quotes']:
                    return data['quotes']['quote']
        except Exception as e:
            print(f"Error fetching quote: {e}")
        return None

    def calculate_breakeven_percentage(self, current_price, strike_price, premium, option_type="call"):
        """Calculate percentage move needed to break even"""
        try:
            if option_type.lower() == "call":
                breakeven_price = strike_price + premium
                percentage_move = ((breakeven_price - current_price) / current_price) * 100
            else:  # put
                breakeven_price = strike_price - premium
                percentage_move = ((current_price - breakeven_price) / current_price) * 100
                
            return {
                'breakeven_price': round(breakeven_price, 2),
                'percentage_move_needed': round(percentage_move, 2),
                'current_price': current_price,
                'premium': premium,
                'strike': strike_price
            }
        except Exception as e:
            print(f"Error calculating breakeven: {e}")
            return None

    def get_closest_itm_options(self, current_price, option_chain):
        """Get closest in-the-money call and put options - FIXED None handling"""
        # FIX 1: Check if option_chain is None
        if not option_chain:
            print("DEBUG: option_chain is None")
            return None, None
            
        # FIX 2: Check if 'options' key exists
        if 'options' not in option_chain:
            print(f"DEBUG: 'options' key not in option_chain. Keys: {list(option_chain.keys())}")
            return None, None
            
        # FIX 3: Check if 'option' key exists within 'options'
        if 'option' not in option_chain['options']:
            print(f"DEBUG: 'option' key not in options. Keys: {list(option_chain['options'].keys()) if option_chain['options'] else 'None'}")
            return None, None
            
        options = option_chain['options']['option']
        
        # FIX 4: Check if options data exists
        if not options:
            print("DEBUG: options data is empty")
            return None, None
            
        if not isinstance(options, list):
            options = [options]
            
        # FIX 5: Check if we have valid options data
        valid_options = [opt for opt in options if opt and isinstance(opt, dict) and 'option_type' in opt and 'strike' in opt]
        if not valid_options:
            print("DEBUG: No valid options found in data")
            return None, None
        
        calls = [opt for opt in valid_options if opt['option_type'] == 'call']
        puts = [opt for opt in valid_options if opt['option_type'] == 'put']
        
        # Find closest ITM call (strike <= current_price)
        try:
            itm_calls = [c for c in calls if float(c['strike']) <= current_price]
            closest_call = max(itm_calls, key=lambda x: float(x['strike'])) if itm_calls else None
        except Exception as e:
            print(f"Error processing calls: {e}")
            closest_call = None
        
        # Find closest ITM put (strike >= current_price)  
        try:
            itm_puts = [p for p in puts if float(p['strike']) >= current_price]
            closest_put = min(itm_puts, key=lambda x: float(x['strike'])) if itm_puts else None
        except Exception as e:
            print(f"Error processing puts: {e}")
            closest_put = None
        
        return closest_call, closest_put

    def get_premium_efficiency_data(self, symbol="SPY"):
        """Get current premium efficiency data - FIXED with None checks"""
        print(f"DEBUG: Starting premium efficiency analysis for {symbol}")
        
        # FIX 1: Check stock quote
        stock_data = self.get_stock_quote(symbol)
        if not stock_data:
            print("DEBUG: Failed to get stock quote")
            return None
            
        try:
            current_price = float(stock_data['last'])
            print(f"DEBUG: Current price: ${current_price:.2f}")
        except (KeyError, ValueError, TypeError) as e:
            print(f"DEBUG: Error getting current price: {e}")
            return None
        
        # FIX 2: Check option chain
        option_chain = self.get_option_chain(symbol)
        if not option_chain:
            print("DEBUG: Failed to get option chain")
            return None
        
        # FIX 3: Try to get options with error handling
        try:
            closest_call, closest_put = self.get_closest_itm_options(current_price, option_chain)
        except Exception as e:
            print(f"DEBUG: Error getting closest options: {e}")
            return None
        
        result = {
            'current_price': current_price,
            'timestamp': datetime.now(),
            'call_analysis': None,
            'put_analysis': None
        }
        
        # FIX 4: Process call data with error handling
        if closest_call:
            try:
                call_bid = float(closest_call.get('bid', 0))
                call_ask = float(closest_call.get('ask', 0))
                
                if call_bid > 0 and call_ask > 0:
                    call_premium = (call_bid + call_ask) / 2
                    call_analysis = self.calculate_breakeven_percentage(
                        current_price, float(closest_call['strike']), call_premium, "call"
                    )
                    if call_analysis:
                        call_analysis['bid_ask_spread'] = call_ask - call_bid
                        result['call_analysis'] = call_analysis
                        print(f"DEBUG: Call analysis completed: Strike ${closest_call['strike']}, Premium ${call_premium:.2f}")
                else:
                    print(f"DEBUG: Invalid call bid/ask: bid={call_bid}, ask={call_ask}")
            except Exception as e:
                print(f"DEBUG: Error processing call: {e}")
        else:
            print("DEBUG: No closest call found")
            
        # FIX 5: Process put data with error handling
        if closest_put:
            try:
                put_bid = float(closest_put.get('bid', 0))
                put_ask = float(closest_put.get('ask', 0))
                
                if put_bid > 0 and put_ask > 0:
                    put_premium = (put_bid + put_ask) / 2
                    put_analysis = self.calculate_breakeven_percentage(
                        current_price, float(closest_put['strike']), put_premium, "put"
                    )
                    if put_analysis:
                        put_analysis['bid_ask_spread'] = put_ask - put_bid
                        result['put_analysis'] = put_analysis
                        print(f"DEBUG: Put analysis completed: Strike ${closest_put['strike']}, Premium ${put_premium:.2f}")
                else:
                    print(f"DEBUG: Invalid put bid/ask: bid={put_bid}, ask={put_ask}")
            except Exception as e:
                print(f"DEBUG: Error processing put: {e}")
        else:
            print("DEBUG: No closest put found")
            
        # Return result even if some analysis failed
        if result['call_analysis'] or result['put_analysis']:
            print("DEBUG: Premium efficiency analysis successful")
            return result
        else:
            print("DEBUG: No valid options analysis completed")
            return None

    def analyze_historical_2pm_4pm_returns(self, symbol="SPY", days_back=30):
        """Analyze historical 2-4 PM returns - SAFE VERSION"""
        print(f"DEBUG: Starting historical analysis for {symbol}")
        
        # Skip this analysis entirely if APIs are problematic
        try:
            # Quick test of API access
            test_quote = self.get_stock_quote(symbol)
            if not test_quote:
                print("DEBUG: Stock quote test failed, skipping historical analysis")
                return None
        except:
            print("DEBUG: API test failed, skipping historical analysis")
            return None
        
        print("DEBUG: Historical analysis disabled in emergency mode")
        return None

    def test_api_connection(self):
        """Test if the API token works for basic quotes"""
        headers = {'Authorization': f'Bearer {self.api_token}', 'Accept': 'application/json'}
        try:
            response = requests.get(f"{self.base_url}/markets/quotes?symbols=SPY", headers=headers, timeout=10)
            print(f"API Test - Status: {response.status_code}, Response: {response.text[:200]}")
            return response.status_code == 200
        except Exception as e:
            print(f"API Test failed: {e}")
            return False
