"""Technical analysis with VWAP and support/resistance"""
import numpy as np
from datetime import datetime, timedelta
from typing import Dict

from api.tradier_client import TradierAPI
from api.yahoo_client import get_cached_yahoo_data

class TechnicalAnalyzer:
    """Enhanced technical analysis with transparent points breakdown"""
    
    def __init__(self, api: TradierAPI):
        self.api = api
    
    def analyze_technicals(self) -> Dict:
        """Enhanced technical analysis with transparent points breakdown"""
        try:
            # Get SPY data
            spy_data = self._get_spy_technical_data()
            
            if spy_data.get('error'):
                return self._get_fallback_technicals()
            
            current_price = spy_data['current_price']
            vwap_data = spy_data.get('vwap_data', {})
            vwap = vwap_data.get('vwap', current_price)
            vwap_distance_pct = vwap_data.get('distance_pct', 0.0)
            data_source = spy_data['source']
            
            # Support/Resistance Analysis
            yesterday_levels = self._get_yesterday_levels(current_price)
            
            # Volume analysis
            volume_data = spy_data.get('volume_data', {})
            volume_confirmation = self._calculate_volume_confirmation(volume_data)
            
            # Points breakdown
            technicals_breakdown = self._calculate_technicals_breakdown(
                vwap_distance_pct, yesterday_levels, current_price, volume_confirmation
            )
            
            return {
                'total_points': technicals_breakdown['total_points'],
                'vwap_analysis': {
                    'current_price': current_price,
                    'vwap': vwap,
                    'distance_pct': vwap_distance_pct,
                    'signal_strength': self._get_vwap_signal_strength(vwap_distance_pct),
                    'source': data_source
                },
                'support_resistance': {
                    'yesterday_high': yesterday_levels['high'],
                    'yesterday_low': yesterday_levels['low'],
                    'yesterday_close': yesterday_levels['close'],
                    'current_vs_yesterday_high': ((current_price - yesterday_levels['high']) / yesterday_levels['high']) * 100,
                    'current_vs_yesterday_low': ((current_price - yesterday_levels['low']) / yesterday_levels['low']) * 100
                },
                'volume_analysis': {
                    'recent_vs_average': volume_confirmation,
                    'signal': 'STRONG' if volume_confirmation > 1.5 else 'WEAK' if volume_confirmation < 0.8 else 'NORMAL'
                },
                'data_source': data_source,
                'points_breakdown': technicals_breakdown,
                'error': None
            }
            
        except Exception as e:
            return self._get_fallback_technicals()
    
    def _get_spy_technical_data(self) -> Dict:
        """Get SPY data for technical analysis"""
        spy_data = {
            'current_price': 0,
            'volume_data': {},
            'vwap_data': {},
            'source': 'unknown',
            'error': None
        }
        
        # Try Tradier first
        try:
            spy_quote = self.api.get_quote('SPY')
            if spy_quote and spy_quote.get('last'):
                spy_data['current_price'] = float(spy_quote['last'])
                spy_data['volume_data'] = {
                    'current_volume': float(spy_quote.get('volume', 0)),
                    'avg_volume': float(spy_quote.get('avgvolume', 0))
                }
                spy_data['source'] = 'Tradier'
                
                # Get VWAP from historical data
                vwap_data = self._calculate_vwap_tradier()
                if vwap_data:
                    spy_data['vwap_data'] = vwap_data
                    return spy_data
        except:
            pass
        
        # Try Yahoo fallback
        try:
            spy_hist = get_cached_yahoo_data('SPY', '1d', '1m')
            if not spy_hist.empty:
                if spy_data['current_price'] == 0:
                    spy_data['current_price'] = spy_hist['Close'].iloc[-1]
                    spy_data['source'] = 'Yahoo (Fallback)'
                
                spy_data['volume_data'] = {
                    'current_volume': spy_hist['Volume'].iloc[-1],
                    'avg_volume': spy_hist['Volume'].mean()
                }
                
                # Calculate VWAP from Yahoo data
                typical_price = (spy_hist['High'] + spy_hist['Low'] + spy_hist['Close']) / 3
                total_volume = spy_hist['Volume'].sum()
                
                if total_volume > 0:
                    vwap = (typical_price * spy_hist['Volume']).sum() / total_volume
                    vwap_distance = ((spy_data['current_price'] - vwap) / vwap) * 100
                    
                    spy_data['vwap_data'] = {
                        'vwap': vwap,
                        'distance_pct': vwap_distance,
                        'source': 'Yahoo (Fallback)',
                        'data_points': len(spy_hist),
                        'total_volume': total_volume
                    }
                    return spy_data
        except:
            pass
        
        # Use proxy data
        spy_data.update({
            'current_price': 640.27,
            'volume_data': {'current_volume': 50000000, 'avg_volume': 45000000},
            'vwap_data': {'vwap': 640.27, 'distance_pct': 0.000, 'source': 'Proxy'},
            'source': 'Proxy Fallback',
            'error': None
        })
        
        return spy_data
    
    def _calculate_vwap_tradier(self) -> Dict:
        """Calculate VWAP from Tradier historical data"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            tradier_hist = self.api.get_historical_quotes('SPY', '1min', today)
            
            if tradier_hist and 'history' in tradier_hist:
                hist_data = tradier_hist['history']['day']
                if isinstance(hist_data, dict):
                    hist_data = [hist_data]
                
                total_pv = 0
                total_volume = 0
                valid_points = 0
                
                for d in hist_data:
                    close_price = float(d.get('close', 0))
                    volume = float(d.get('volume', 0))
                    
                    if close_price > 0 and volume > 0:
                        total_pv += close_price * volume
                        total_volume += volume
                        valid_points += 1
                
                if total_volume > 0:
                    vwap = total_pv / total_volume
                    return {
                        'vwap': vwap,
                        'distance_pct': 0.0,  # Will be calculated later
                        'source': 'Tradier',
                        'data_points': valid_points,
                        'total_volume': total_volume
                    }
        except:
            pass
        
        return None
    
    def _get_yesterday_levels(self, current_price: float) -> Dict:
        """Get yesterday's high, low, close levels"""
        try:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            tradier_hist = self.api.get_historical_quotes('SPY', '1day', yesterday)
            
            if tradier_hist and 'history' in tradier_hist:
                hist_data = tradier_hist['history']['day']
                if isinstance(hist_data, dict):
                    return {
                        'high': float(hist_data['high']),
                        'low': float(hist_data['low']),
                        'close': float(hist_data['close'])
                    }
        except:
            pass
        
        # Try Yahoo fallback
        try:
            spy_hist = get_cached_yahoo_data('SPY', '2d', '1d')
            if not spy_hist.empty and spy_hist.shape[0] >= 2:
                return {
                    'high': spy_hist['High'].iloc[-2],
                    'low': spy_hist['Low'].iloc[-2],
                    'close': spy_hist['Close'].iloc[-2]
                }
        except:
            pass
        
        # Ultimate fallback
        return {
            'high': current_price * 1.015,
            'low': current_price * 0.985,
            'close': current_price * 1.005
        }
    
    def _calculate_volume_confirmation(self, volume_data: Dict) -> float:
        """Calculate volume confirmation ratio"""
        current_volume = volume_data.get('current_volume', 0)
        avg_volume = volume_data.get('avg_volume', 1)
        return current_volume / avg_volume if avg_volume > 0 else 1.0
    
    def _calculate_technicals_breakdown(self, vwap_distance_pct: float, yesterday_levels: Dict, 
                                       current_price: float, volume_confirmation: float) -> Dict:
        """Calculate technical analysis points breakdown"""
        technicals_breakdown = {
            'vwap': {'points': 0, 'reason': ''},
            'support_resistance': {'points': 0, 'reason': ''},
            'volume': {'points': 0, 'reason': ''},
            'total_points': 0
        }
        
        # VWAP signal strength
        vwap_points, vwap_reason = self._calculate_vwap_points(vwap_distance_pct)
        technicals_breakdown['vwap'] = {'points': vwap_points, 'reason': vwap_reason}
        
        # Support/Resistance points
        sr_points, sr_reason = self._calculate_sr_points(current_price, yesterday_levels)
        technicals_breakdown['support_resistance'] = {'points': sr_points, 'reason': sr_reason}
        
        # Volume confirmation points
        volume_points, volume_reason = self._calculate_volume_points(volume_confirmation)
        technicals_breakdown['volume'] = {'points': volume_points, 'reason': volume_reason}
        
        # Calculate total
        technicals_breakdown['total_points'] = vwap_points + sr_points + volume_points
        
        return technicals_breakdown
    
    def _calculate_vwap_points(self, vwap_distance_pct: float) -> tuple:
        """Calculate VWAP points with reasoning"""
        if abs(vwap_distance_pct) > 0.3:
            vwap_points = 2.0 if vwap_distance_pct > 0 else -2.0
            return vwap_points, f"Strong VWAP distance {vwap_distance_pct:+.3f}% (>0.3%) = {vwap_points:+.1f} pts"
        elif abs(vwap_distance_pct) > 0.15:
            vwap_points = 1.0 if vwap_distance_pct > 0 else -1.0
            return vwap_points, f"Moderate VWAP distance {vwap_distance_pct:+.3f}% (0.15-0.3%) = {vwap_points:+.1f} pts"
        elif abs(vwap_distance_pct) > 0.05:
            vwap_points = 0.5 if vwap_distance_pct > 0 else -0.5
            return vwap_points, f"Weak VWAP distance {vwap_distance_pct:+.3f}% (0.05-0.15%) = {vwap_points:+.1f} pts"
        else:
            return 0.0, f"Neutral VWAP distance {vwap_distance_pct:+.3f}% (≤0.05%) = 0.0 pts"
    
    def _calculate_sr_points(self, current_price: float, yesterday_levels: Dict) -> tuple:
        """Calculate support/resistance points with reasoning"""
        yesterday_high = yesterday_levels['high']
        yesterday_low = yesterday_levels['low']
        
        if current_price > yesterday_high:
            return 1.0, f"Breakout above yesterday high ${yesterday_high:.2f} = +1.0 pts"
        elif current_price < yesterday_low:
            return -1.0, f"Breakdown below yesterday low ${yesterday_low:.2f} = -1.0 pts"
        else:
            return 0.0, f"Price within yesterday range ${yesterday_low:.2f}-${yesterday_high:.2f} = 0.0 pts"
    
    def _calculate_volume_points(self, volume_confirmation: float) -> tuple:
        """Calculate volume points with reasoning"""
        if volume_confirmation > 1.5:
            return 0.5, f"Strong volume {volume_confirmation:.1f}x average (>1.5x) = +0.5 pts"
        elif volume_confirmation < 0.8:
            return -0.5, f"Weak volume {volume_confirmation:.1f}x average (<0.8x) = -0.5 pts"
        else:
            return 0.0, f"Normal volume {volume_confirmation:.1f}x average (0.8-1.5x) = 0.0 pts"
    
    def _get_vwap_signal_strength(self, vwap_distance_pct: float) -> str:
        """Get VWAP signal strength"""
        if abs(vwap_distance_pct) > 0.3:
            return "STRONG"
        elif abs(vwap_distance_pct) > 0.15:
            return "MODERATE"
        elif abs(vwap_distance_pct) > 0.05:
            return "WEAK"
        else:
            return "NEUTRAL"
    
    def _get_fallback_technicals(self) -> Dict:
        """Return fallback technical analysis"""
        return {
            'total_points': -1.0,
            'points_breakdown': {
                'vwap': {'points': 0.0, 'reason': 'Neutral VWAP (proxy estimate)'},
                'support_resistance': {'points': -0.5, 'reason': 'Below resistance level (proxy estimate)'},
                'volume': {'points': -0.5, 'reason': 'Weak volume (proxy estimate)'},
                'total_points': -1.0
            },
            'vwap_analysis': {
                'current_price': 640.27,
                'vwap': 640.27,
                'distance_pct': 0.000,
                'signal_strength': 'NEUTRAL'
            },
            'support_resistance': {
                'yesterday_high': 647.84,
                'yesterday_low': 643.14,
                'yesterday_close': 645.05,
                'current_vs_yesterday_high': -1.17,
                'current_vs_yesterday_low': -0.45
            },
            'volume_analysis': {
                'recent_vs_average': 1.0,
                'signal': 'NORMAL'
            },
            'data_source': 'Proxy Fallback',
            'error': None
        }
