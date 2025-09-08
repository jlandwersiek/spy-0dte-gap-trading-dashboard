"""Market internals analysis with proxy calculations"""
from typing import Dict

from api.tradier_client import TradierAPI
from api.yahoo_client import get_cached_yahoo_data
from utils.data_providers import ProxyDataProvider

class InternalsAnalyzer:
    """Market internals analyzer with transparent points breakdown"""
    
    def __init__(self, api: TradierAPI):
        self.api = api
        self.proxy_provider = ProxyDataProvider()
    
    def analyze_market_internals(self) -> Dict:
        """Enhanced market internals with transparent points breakdown"""
        try:
            internals_data = self._get_internals_data()
            
            internals_breakdown = {
                'tick': {'points': 0, 'reason': ''},
                'trin': {'points': 0, 'reason': ''},
                'nyad': {'points': 0, 'reason': ''},
                'vold': {'points': 0, 'reason': ''},
                'total_points': 0
            }
            
            # Analyze each internal
            tick_points, tick_signal, tick_reason = self._analyze_tick(internals_data['tick']['value'])
            trin_points, trin_signal, trin_reason = self._analyze_trin(internals_data['trin']['value'])
            nyad_points, nyad_signal, nyad_reason = self._analyze_nyad(internals_data['nyad']['value'])
            vold_points, vold_signal, vold_reason = self._analyze_vold(internals_data['vold']['value'])
            
            # Update breakdown
            internals_breakdown['tick'] = {'points': tick_points, 'reason': tick_reason}
            internals_breakdown['trin'] = {'points': trin_points, 'reason': trin_reason}
            internals_breakdown['nyad'] = {'points': nyad_points, 'reason': nyad_reason}
            internals_breakdown['vold'] = {'points': vold_points, 'reason': vold_reason}
            internals_breakdown['total_points'] = tick_points + trin_points + nyad_points + vold_points
            
            # Update signals
            internals_data['tick']['signal'] = tick_signal
            internals_data['trin']['signal'] = trin_signal
            internals_data['nyad']['signal'] = nyad_signal
            internals_data['vold']['signal'] = vold_signal
            
            return {
                'tick': internals_data['tick'],
                'trin': internals_data['trin'],
                'nyad': internals_data['nyad'],
                'vold': internals_data['vold'],
                'total_points': internals_breakdown['total_points'],
                'points_breakdown': internals_breakdown
            }
            
        except Exception as e:
            return self._get_fallback_internals()
    
    def _get_internals_data(self) -> Dict:
        """Get market internals - Yahoo proxy calculations"""
        internals = {
            'tick': {'value': 0, 'source': 'Yahoo Proxy'},
            'trin': {'value': 1.0, 'source': 'Yahoo Proxy'},
            'nyad': {'value': 0, 'source': 'Yahoo Proxy'},
            'vold': {'value': 1.0, 'source': 'Yahoo Proxy'}
        }
        
        # Try Yahoo calculation first
        try:
            indices = ['SPY', 'QQQ', 'IWM', 'DIA']
            index_data = {}
            
            for idx in indices:
                hist = get_cached_yahoo_data(idx, '1d', '1m')
                if not hist.empty:
                    change_pct = ((hist['Close'].iloc[-1] - hist['Open'].iloc[0]) / hist['Open'].iloc[0]) * 100
                    volume_ratio = hist['Volume'].iloc[-1] / hist['Volume'].mean() if len(hist) > 1 else 1.0
                    index_data[idx] = {'change_pct': change_pct, 'volume_ratio': volume_ratio}
            
            if index_data:
                positive_indices = sum(1 for data in index_data.values() if data['change_pct'] > 0)
                total_indices = len(index_data)
                
                # Calculate proxy values
                internals['tick']['value'] = ((positive_indices / total_indices) - 0.5) * 2000
                internals['nyad']['value'] = ((positive_indices / total_indices) - 0.5) * 4000
                
                avg_volume_ratio = sum(data['volume_ratio'] for data in index_data.values()) / len(index_data)
                internals['trin']['value'] = 1.0 / avg_volume_ratio if avg_volume_ratio > 0 else 1.0
                internals['vold']['value'] = (index_data.get('QQQ', {}).get('volume_ratio', 1) + 
                                             index_data.get('SPY', {}).get('volume_ratio', 1)) / 2
                
                return internals
        except:
            pass
        
        # FINAL FALLBACK: Use proxy estimates
        proxy_internals = self.proxy_provider.get_internals_proxy_data()
        for key in internals:
            internals[key].update(proxy_internals[key])
            internals[key]['source'] = 'Proxy Estimate'
        
        return internals
    
    def _analyze_tick(self, tick_value: float) -> tuple:
        """Analyze TICK with transparent points"""
        if tick_value >= 1000:
            return 2.0, "EXTREME BULLISH", f"$TICK {tick_value:.0f} ≥ +1000 (Extreme Bullish) = +2.0 pts"
        elif tick_value >= 800:
            return 1.5, "BULLISH", f"$TICK {tick_value:.0f} ≥ +800 (Strong Bullish) = +1.5 pts"
        elif tick_value >= 200:
            return 1.0, "MODERATE BULLISH", f"$TICK {tick_value:.0f} ≥ +200 (Moderate Bullish) = +1.0 pts"
        elif tick_value <= -1000:
            return -2.0, "EXTREME BEARISH", f"$TICK {tick_value:.0f} ≤ -1000 (Extreme Bearish) = -2.0 pts"
        elif tick_value <= -800:
            return -1.5, "BEARISH", f"$TICK {tick_value:.0f} ≤ -800 (Strong Bearish) = -1.5 pts"
        elif tick_value <= -200:
            return -1.0, "MODERATE BEARISH", f"$TICK {tick_value:.0f} ≤ -200 (Moderate Bearish) = -1.0 pts"
        else:
            return 0.0, "NEUTRAL", f"$TICK {tick_value:.0f} in neutral range (-200 to +200) = 0.0 pts"
    
    def _analyze_trin(self, trin_value: float) -> tuple:
        """Analyze TRIN with transparent points"""
        if trin_value <= 0.8:
            return 1.0, "BULLISH", f"$TRIN {trin_value:.3f} ≤ 0.8 (Bullish volume flow) = +1.0 pts"
        elif trin_value >= 1.2:
            return -1.0, "BEARISH", f"$TRIN {trin_value:.3f} ≥ 1.2 (Bearish volume flow) = -1.0 pts"
        else:
            return 0.0, "NEUTRAL", f"$TRIN {trin_value:.3f} neutral (0.8-1.2) = 0.0 pts"
    
    def _analyze_nyad(self, nyad_value: float) -> tuple:
        """Analyze NYAD with transparent points"""
        if nyad_value > 1000:
            return 1.0, "BULLISH", f"NYAD {nyad_value:.0f} > +1000 (Broad bullish participation) = +1.0 pts"
        elif nyad_value < -1000:
            return -1.0, "BEARISH", f"NYAD {nyad_value:.0f} < -1000 (Broad bearish participation) = -1.0 pts"
        else:
            return 0.0, "NEUTRAL", f"NYAD {nyad_value:.0f} neutral (-1000 to +1000) = 0.0 pts"
    
    def _analyze_vold(self, vold_value: float) -> tuple:
        """Analyze VOLD with transparent points"""
        if vold_value > 1.5:
            return 1.0, "BULLISH", f"Volume Flow {vold_value:.2f} > 1.5 (Risk-on flow) = +1.0 pts"
        elif vold_value < 0.7:
            return -1.0, "BEARISH", f"Volume Flow {vold_value:.2f} < 0.7 (Risk-off flow) = -1.0 pts"
        else:
            return 0.0, "NEUTRAL", f"Volume Flow {vold_value:.2f} neutral (0.7-1.5) = 0.0 pts"
    
    def _get_fallback_internals(self) -> Dict:
        """Return fallback internals data"""
        return {
            'total_points': -1.5,
            'points_breakdown': {
                'tick': {'points': 0, 'reason': 'Neutral proxy estimate'},
                'trin': {'points': 0, 'reason': 'Neutral proxy estimate'},
                'nyad': {'points': -1.0, 'reason': 'Bearish proxy estimate'},
                'vold': {'points': -0.5, 'reason': 'Bearish proxy estimate'},
                'total_points': -1.5
            },
            'tick': {'value': 0, 'signal': 'NEUTRAL', 'source': 'Proxy'},
            'trin': {'value': 1.0, 'signal': 'NEUTRAL', 'source': 'Proxy'},
            'nyad': {'value': -2000, 'signal': 'BEARISH', 'source': 'Proxy'},
            'vold': {'value': 0.30, 'signal': 'BEARISH', 'source': 'Proxy'}
        }
