"""Market internals analysis - EMERGENCY FIX VERSION"""
from typing import Dict
import time
import signal

from api.tradier_client import TradierAPI
from api.yahoo_client import get_cached_yahoo_data
from utils.data_providers import ProxyDataProvider

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

class InternalsAnalyzer:
    """EMERGENCY VERSION - Fast fallback when APIs fail"""
    
    def __init__(self, api: TradierAPI):
        self.api = api
        self.proxy_provider = ProxyDataProvider()
        self.emergency_mode = True  # Enable emergency mode by default
        
        # Simplified proxy universe for emergency mode
        self.emergency_symbols = ['SPY', 'QQQ']  # Only 2 symbols
        
        # Real breadth symbols to try
        self.breadth_symbols = {
            'tick': '$TICK',
            'trin': '$TRIN', 
            'nyad': '$NYAD'
        }
    
    def analyze_market_internals(self) -> Dict:
        """EMERGENCY VERSION - Fast analysis with timeouts"""
        print("Starting market internals analysis...")
        
        try:
            # Try real breadth data with short timeout
            real_breadth_data = self._get_real_breadth_data_fast()
            
            if real_breadth_data['data_quality'] == 'REAL':
                print("Using real breadth data")
                return self._process_real_breadth_data(real_breadth_data)
            
            # Emergency mode - use minimal proxy
            print("Using emergency proxy mode")
            return self._get_emergency_proxy_internals()
                
        except Exception as e:
            print(f"Market internals error: {e}")
            return self._get_emergency_fallback()
    
    def _get_real_breadth_data_fast(self) -> Dict:
        """Fast real breadth attempt with 5-second timeout"""
        real_data = {
            'symbols_found': [],
            'symbols_failed': [],
            'data_quality': 'FAILED',
            'breadth_values': {}
        }
        
        try:
            # Set 5-second timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)
            
            # Try only 3 core symbols
            symbols_string = ','.join(['$TICK', '$TRIN', '$NYAD'])
            print(f"Trying real breadth with 5s timeout: {symbols_string}")
            
            bulk_quotes = self.api.get_quotes_bulk(symbols_string)
            
            signal.alarm(0)  # Cancel timeout
            
            if bulk_quotes:
                for symbol_key, tradier_symbol in [('tick', '$TICK'), ('trin', '$TRIN'), ('nyad', '$NYAD')]:
                    if tradier_symbol in bulk_quotes:
                        quote = bulk_quotes[tradier_symbol]
                        if quote and quote.get('last') is not None:
                            real_data['breadth_values'][symbol_key] = {
                                'value': float(quote['last']),
                                'change': float(quote.get('change', 0)),
                                'source': 'Tradier Real Data'
                            }
                            real_data['symbols_found'].append(tradier_symbol)
                
                if len(real_data['symbols_found']) >= 2:
                    real_data['data_quality'] = 'REAL'
                    return real_data
                    
        except TimeoutError:
            print("Real breadth timeout after 5 seconds")
        except Exception as e:
            print(f"Real breadth error: {e}")
        finally:
            signal.alarm(0)  # Ensure timeout is cancelled
        
        return real_data
    
    def _get_emergency_proxy_internals(self) -> Dict:
        """EMERGENCY PROXY - Only 2 symbols with timeouts"""
        print("Starting emergency proxy with 2 symbols...")
        
        symbol_data = {}
        failed_symbols = []
        
        # Only try SPY and QQQ with strict timeouts
        for symbol in self.emergency_symbols:
            try:
                print(f"Trying {symbol} with timeout...")
                
                # Set 3-second timeout per symbol
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(3)
                
                hist = get_cached_yahoo_data(symbol, '1d', '5m')  # Use 5m instead of 1m
                
                signal.alarm(0)  # Cancel timeout
                
                if not hist.empty:
                    open_price = float(hist['Open'].iloc[0])
                    close_price = float(hist['Close'].iloc[-1])
                    current_volume = float(hist['Volume'].iloc[-1])
                    avg_volume = float(hist['Volume'].mean())
                
                    change_pct = ((close_price - open_price) / open_price) * 100
                    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                
                    symbol_data[symbol] = {
                        'change_pct': float(change_pct),
                        'volume_ratio': float(volume_ratio),
                        'advancing': bool(change_pct > 0)
                    }
                    print(f"✅ {symbol}: {change_pct:+.2f}%")
                else:
                    failed_symbols.append(f"{symbol} (empty data)")
                    print(f"❌ {symbol}: Empty data")
                    
            except TimeoutError:
                failed_symbols.append(f"{symbol} (timeout)")
                print(f"❌ {symbol}: Timeout after 3 seconds")
            except Exception as e:
                failed_symbols.append(f"{symbol} (error: {str(e)})")
                print(f"❌ {symbol}: Error - {str(e)}")
            finally:
                signal.alarm(0)  # Ensure timeout is cancelled
        
        # If we got at least 1 symbol, proceed
        if len(symbol_data) >= 1:
            print(f"Emergency proxy proceeding with {len(symbol_data)} symbols")
            
            # Simple calculations
            advancing_count = sum(1 for data in symbol_data.values() if data['advancing'])
            total_count = len(symbol_data)
            
            if total_count > 0:
                advance_pct = (advancing_count / total_count - 0.5) * 2
            else:
                advance_pct = 0
            
            # Simple proxy values
            proxy_tick = advance_pct * 1000  # -1000 to +1000
            proxy_trin = 1.0 / (1.0 + advance_pct) if advance_pct > -0.9 else 2.0
            proxy_nyad = advance_pct * 2000  # -2000 to +2000
            proxy_vold = 1.0 + advance_pct  # 0 to 2
            
            # Calculate points
            tick_points, tick_signal, tick_reason = self._analyze_tick(proxy_tick)
            trin_points, trin_signal, trin_reason = self._analyze_trin(proxy_trin)
            nyad_points, nyad_signal, nyad_reason = self._analyze_nyad(proxy_nyad)
            vold_points, vold_signal, vold_reason = self._analyze_vold(proxy_vold)
            
            internals_breakdown = {
                'tick': {'points': tick_points, 'reason': f"EMERGENCY PROXY ({len(symbol_data)} ETFs): {tick_reason}"},
                'trin': {'points': trin_points, 'reason': f"EMERGENCY PROXY ({len(symbol_data)} ETFs): {trin_reason}"},
                'nyad': {'points': nyad_points, 'reason': f"EMERGENCY PROXY ({len(symbol_data)} ETFs): {nyad_reason}"},
                'vold': {'points': vold_points, 'reason': f"EMERGENCY PROXY ({len(symbol_data)} ETFs): {vold_reason}"},
                'total_points': tick_points + trin_points + nyad_points + vold_points
            }
            
            return {
                'tick': {'value': proxy_tick, 'signal': tick_signal, 'source': f'Emergency Proxy ({len(symbol_data)} ETFs)'},
                'trin': {'value': proxy_trin, 'signal': trin_signal, 'source': f'Emergency Proxy ({len(symbol_data)} ETFs)'},
                'nyad': {'value': proxy_nyad, 'signal': nyad_signal, 'source': f'Emergency Proxy ({len(symbol_data)} ETFs)'},
                'vold': {'value': proxy_vold, 'signal': vold_signal, 'source': f'Emergency Proxy ({len(symbol_data)} ETFs)'},
                'total_points': internals_breakdown['total_points'],
                'points_breakdown': internals_breakdown,
                'data_quality': f'EMERGENCY PROXY ({len(symbol_data)}/2 ETFs)',
                'breadth_score': internals_breakdown['total_points'],
                'emergency_mode': True
            }
        
        # If even emergency proxy fails, use static fallback
        print("Emergency proxy failed, using static fallback")
        return self._get_emergency_fallback()
    
    def _get_emergency_fallback(self) -> Dict:
        """Static fallback when everything fails"""
        print("Using static emergency fallback")
        
        # Use proxy provider data
        proxy_internals = self.proxy_provider.get_internals_proxy_data()
        
        internals_breakdown = {
            'tick': {'points': -0.5, 'reason': 'EMERGENCY FALLBACK: Bearish proxy estimate'},
            'trin': {'points': 0.0, 'reason': 'EMERGENCY FALLBACK: Neutral proxy estimate'},
            'nyad': {'points': -1.0, 'reason': 'EMERGENCY FALLBACK: Bearish proxy estimate'},
            'vold': {'points': -0.5, 'reason': 'EMERGENCY FALLBACK: Bearish proxy estimate'},
            'total_points': -2.0
        }
        
        return {
            'tick': {'value': proxy_internals['tick']['value'], 'signal': proxy_internals['tick']['signal'], 'source': 'Emergency Fallback'},
            'trin': {'value': proxy_internals['trin']['value'], 'signal': proxy_internals['trin']['signal'], 'source': 'Emergency Fallback'},
            'nyad': {'value': proxy_internals['nyad']['value'], 'signal': proxy_internals['nyad']['signal'], 'source': 'Emergency Fallback'},
            'vold': {'value': proxy_internals['vold']['value'], 'signal': proxy_internals['vold']['signal'], 'source': 'Emergency Fallback'},
            'total_points': internals_breakdown['total_points'],
            'points_breakdown': internals_breakdown,
            'data_quality': 'EMERGENCY FALLBACK',
            'breadth_score': internals_breakdown['total_points'],
            'emergency_mode': True
        }
    
    def _process_real_breadth_data(self, real_data: Dict) -> Dict:
        """Process real breadth data into analysis"""
        breadth_values = real_data['breadth_values']

        internals_breakdown = {
            'tick': {'points': 0, 'reason': ''},
            'trin': {'points': 0, 'reason': ''},
            'nyad': {'points': 0, 'reason': ''},
            'vold': {'points': 0, 'reason': ''},
            'total_points': 0
        }

        total_points = 0
        
        # Analyze TICK
        if 'tick' in breadth_values:
            tick_value = breadth_values['tick']['value']
            tick_points, tick_signal, tick_reason = self._analyze_tick(tick_value)
            internals_breakdown['tick'] = {'points': tick_points, 'reason': tick_reason}
            total_points += tick_points

        # Analyze TRIN
        if 'trin' in breadth_values:
            trin_value = breadth_values['trin']['value']
            trin_points, trin_signal, trin_reason = self._analyze_trin(trin_value)
            internals_breakdown['trin'] = {'points': trin_points, 'reason': trin_reason}
            total_points += trin_points

        # Analyze NYAD
        if 'nyad' in breadth_values:
            nyad_value = breadth_values['nyad']['value']
            nyad_points, nyad_signal, nyad_reason = self._analyze_nyad(nyad_value)
            internals_breakdown['nyad'] = {'points': nyad_points, 'reason': nyad_reason}
            total_points += nyad_points

        # Estimate VOLD
        vold_value = 1.0
        if 'tick' in breadth_values and 'trin' in breadth_values:
            tick_val = breadth_values['tick']['value']
            trin_val = breadth_values['trin']['value']
            if tick_val > 500 and trin_val < 0.9:
                vold_value = 1.8
            elif tick_val < -500 and trin_val > 1.1:
                vold_value = 0.4
        
        vold_points, vold_signal, vold_reason = self._analyze_vold(vold_value)
        internals_breakdown['vold'] = {'points': vold_points, 'reason': vold_reason}
        total_points += vold_points

        internals_breakdown['total_points'] = total_points

        return {
            'total_points': total_points,
            'points_breakdown': internals_breakdown,
            'data_quality': f'REAL BREADTH DATA ({len(real_data["symbols_found"])} indicators)',
            'symbols_found': real_data['symbols_found'],
            'breadth_score': total_points,
            'tick': {'value': breadth_values.get('tick', {}).get('value', 0), 'signal': self._get_signal_from_points(internals_breakdown['tick']['points']), 'source': 'Tradier Real'},
            'trin': {'value': breadth_values.get('trin', {}).get('value', 1.0), 'signal': self._get_signal_from_points(internals_breakdown['trin']['points']), 'source': 'Tradier Real'},
            'nyad': {'value': breadth_values.get('nyad', {}).get('value', 0), 'signal': self._get_signal_from_points(internals_breakdown['nyad']['points']), 'source': 'Tradier Real'},
            'vold': {'value': vold_value, 'signal': vold_signal, 'source': 'Estimated from Real Data'}
        }
    
    def _get_signal_from_points(self, points: float) -> str:
        """Convert points to signal"""
        if points >= 1.0:
            return "BULLISH"
        elif points <= -1.0:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _analyze_tick(self, tick_value: float) -> tuple:
        """Analyze TICK with transparent points"""
        if tick_value >= 1000:
            return 2.0, "EXTREME BULLISH", f"$TICK {tick_value:.0f} ≥ +1000 (Extreme Bullish) = +2.0 pts"
        elif tick_value >= 200:
            return 1.0, "MODERATE BULLISH", f"$TICK {tick_value:.0f} ≥ +200 (Moderate Bullish) = +1.0 pts"
        elif tick_value <= -1000:
            return -2.0, "EXTREME BEARISH", f"$TICK {tick_value:.0f} ≤ -1000 (Extreme Bearish) = -2.0 pts"
        elif tick_value <= -200:
            return -1.0, "MODERATE BEARISH", f"$TICK {tick_value:.0f} ≤ -200 (Moderate Bearish) = -1.0 pts"
        else:
            return 0.0, "NEUTRAL", f"$TICK {tick_value:.0f} in neutral range = 0.0 pts"
    
    def _analyze_trin(self, trin_value: float) -> tuple:
        """Analyze TRIN with transparent points"""
        if trin_value <= 0.8:
            return 1.0, "BULLISH", f"$TRIN {trin_value:.3f} ≤ 0.8 (Bullish volume flow) = +1.0 pts"
        elif trin_value >= 1.2:
            return -1.0, "BEARISH", f"$TRIN {trin_value:.3f} ≥ 1.2 (Bearish volume flow) = -1.0 pts"
        else:
            return 0.0, "NEUTRAL", f"$TRIN {trin_value:.3f} neutral = 0.0 pts"
    
    def _analyze_nyad(self, nyad_value: float) -> tuple:
        """Analyze NYAD with transparent points"""
        if nyad_value > 1000:
            return 1.0, "BULLISH", f"NYAD {nyad_value:.0f} > +1000 = +1.0 pts"
        elif nyad_value < -1000:
            return -1.0, "BEARISH", f"NYAD {nyad_value:.0f} < -1000 = -1.0 pts"
        else:
            return 0.0, "NEUTRAL", f"NYAD {nyad_value:.0f} neutral = 0.0 pts"
    
    def _analyze_vold(self, vold_value: float) -> tuple:
        """Analyze VOLD with transparent points"""
        if vold_value > 1.5:
            return 1.0, "BULLISH", f"Volume Flow {vold_value:.2f} > 1.5 = +1.0 pts"
        elif vold_value < 0.7:
            return -1.0, "BEARISH", f"Volume Flow {vold_value:.2f} < 0.7 = -1.0 pts"
        else:
            return 0.0, "NEUTRAL", f"Volume Flow {vold_value:.2f} neutral = 0.0 pts"
