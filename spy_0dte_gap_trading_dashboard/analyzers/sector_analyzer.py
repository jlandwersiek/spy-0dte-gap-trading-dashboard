"""Sector leadership analysis"""
from typing import Dict

from config import SECTOR_SYMBOLS, SECTOR_WEIGHTS, SECTOR_NAMES
from api.tradier_client import TradierAPI
from api.yahoo_client import get_cached_yahoo_data
from utils.data_providers import ProxyDataProvider

class SectorAnalyzer:
    """Enhanced sector analysis with transparent points breakdown"""
    
    def __init__(self, api: TradierAPI):
        self.api = api
        self.proxy_provider = ProxyDataProvider()
    
    def analyze_sectors(self) -> Dict:
        """Enhanced sector analysis with transparent points breakdown"""
        try:
            sector_data = self._get_sector_data()
            spy_change, spy_source = self._get_spy_change()
            
            sector_analysis = {}
            total_weighted_score = 0
            strong_sectors = 0
            weak_sectors = 0
            
            sectors_breakdown = {
                'individual_scores': {},
                'leadership_calculation': '',
                'rotation_logic': '',
                'total_weighted_points': 0
            }
            
            # Analyze each sector
            for symbol, data in sector_data.items():
                change_pct = data['change_pct']
                volume_ratio = data['volume'] / data['avg_volume'] if data['avg_volume'] > 0 else 1.0
                relative_strength = change_pct - spy_change
                
                # Calculate strength score
                strength_score, strength_reason = self._calculate_strength_score(
                    relative_strength, volume_ratio
                )
                
                if strength_score >= 2:
                    strong_sectors += 1
                elif strength_score <= -2:
                    weak_sectors += 1
                
                # Weight the score
                weight = SECTOR_WEIGHTS.get(symbol, 0.05)
                weighted_score = strength_score * weight
                total_weighted_score += weighted_score
                
                sector_analysis[symbol] = {
                    'name': SECTOR_NAMES.get(symbol, 'Unknown'),
                    'change_pct': change_pct,
                    'relative_strength': relative_strength,
                    'volume_ratio': volume_ratio,
                    'vwap_distance': 0.0,
                    'strength_score': strength_score,
                    'weight': weight,
                    'source': data['source']
                }
                
                sectors_breakdown['individual_scores'][symbol] = {
                    'strength_score': strength_score,
                    'weight': weight,
                    'weighted_score': weighted_score,
                    'reason': strength_reason
                }
            
            # Calculate leadership and rotation
            leadership_score = strong_sectors - weak_sectors
            rotation_signal, rotation_logic = self._determine_rotation(leadership_score)
            
            sectors_breakdown.update({
                'leadership_calculation': f"Strong sectors ({strong_sectors}) - Weak sectors ({weak_sectors}) = {leadership_score}",
                'rotation_logic': rotation_logic,
                'total_weighted_points': total_weighted_score
            })
            
            return {
                'sectors': sector_analysis,
                'total_points': total_weighted_score,
                'leadership_score': leadership_score,
                'rotation_signal': rotation_signal,
                'strong_sectors': strong_sectors,
                'weak_sectors': weak_sectors,
                'spy_source': spy_source,
                'points_breakdown': sectors_breakdown
            }
            
        except Exception as e:
            return self._get_fallback_sector_analysis()
    
    def _get_sector_data(self) -> Dict:
        """Get sector data with Tradier PRIMARY, Yahoo fallback, Proxy final"""
        sector_data = {}
        
        # PRIMARY: Try Tradier for all sectors first
        try:
            symbols_str = ','.join(SECTOR_SYMBOLS)
            tradier_quotes = self.api.get_quotes_bulk(symbols_str)
            
            if tradier_quotes:
                for symbol in SECTOR_SYMBOLS:
                    if symbol in tradier_quotes:
                        quote = tradier_quotes[symbol]
                        sector_data[symbol] = {
                            'current_price': float(quote.get('last', 0)),
                            'change_pct': float(quote.get('change_percentage', 0)),
                            'volume': float(quote.get('volume', 0)),
                            'avg_volume': float(quote.get('avgvolume', 0)),
                            'source': 'Tradier',
                            'weight': SECTOR_WEIGHTS.get(symbol, 0.05)
                        }
                
                if len(sector_data) == len(SECTOR_SYMBOLS):
                    return sector_data
        except Exception as e:
            pass
        
        # FALLBACK: Yahoo for missing data
        for symbol in SECTOR_SYMBOLS:
            if symbol not in sector_data:
                try:
                    hist = get_cached_yahoo_data(symbol, '1d', '1m')
                    if not hist.empty:
                        change_pct = ((hist['Close'].iloc[-1] - hist['Open'].iloc[0]) / hist['Open'].iloc[0]) * 100
                        sector_data[symbol] = {
                            'current_price': hist['Close'].iloc[-1],
                            'change_pct': change_pct,
                            'volume': hist['Volume'].iloc[-1],
                            'avg_volume': hist['Volume'].mean(),
                            'source': 'Yahoo (Fallback)',
                            'weight': SECTOR_WEIGHTS.get(symbol, 0.05)
                        }
                except:
                    pass
        
        # FINAL FALLBACK: Proxy data
        proxy_sectors = self.proxy_provider.get_sector_proxy_data()
        for symbol in SECTOR_SYMBOLS:
            if symbol not in sector_data:
                proxy = proxy_sectors.get(symbol, {'change_pct': 0, 'volume_ratio': 1.0})
                sector_data[symbol] = {
                    'current_price': 100.0,
                    'change_pct': proxy['change_pct'],
                    'volume': 1000000,
                    'avg_volume': 1000000,
                    'source': 'Proxy Estimate',
                    'weight': SECTOR_WEIGHTS.get(symbol, 0.05)
                }
        
        return sector_data
    
    def _get_spy_change(self) -> tuple:
        """Get SPY performance for relative strength calculation"""
        try:
            spy_quote = self.api.get_quote('SPY')
            if spy_quote and spy_quote.get('change_percentage'):
                return float(spy_quote['change_percentage']), 'Tradier'
        except:
            pass
        
        try:
            spy_data = get_cached_yahoo_data('SPY', '1d', '1m')
            if not spy_data.empty:
                spy_change = ((spy_data['Close'].iloc[-1] - spy_data['Open'].iloc[0]) / spy_data['Open'].iloc[0]) * 100
                return spy_change, 'Yahoo (Fallback)'
        except:
            pass
        
        return -0.75, 'Proxy Estimate'
    
    def _calculate_strength_score(self, relative_strength: float, volume_ratio: float) -> tuple:
        """Calculate sector strength score with reasoning"""
        if relative_strength > 0.5 and volume_ratio > 1.2:
            return 2, f"Strong leader: +{relative_strength:.2f}% vs SPY, {volume_ratio:.1f}x volume = +2 pts"
        elif relative_strength > 0.2:
            return 1, f"Moderate leader: +{relative_strength:.2f}% vs SPY = +1 pts"
        elif relative_strength < -0.5 and volume_ratio > 1.2:
            return -2, f"Strong laggard: {relative_strength:.2f}% vs SPY, {volume_ratio:.1f}x volume = -2 pts"
        elif relative_strength < -0.2:
            return -1, f"Moderate laggard: {relative_strength:.2f}% vs SPY = -1 pts"
        else:
            return 0, f"Neutral: {relative_strength:.2f}% vs SPY = 0 pts"
    
    def _determine_rotation(self, leadership_score: int) -> tuple:
        """Determine market rotation signal"""
        if leadership_score >= 2:
            return "RISK ON", f"Leadership score {leadership_score} ≥ 2 = RISK ON (growth/cyclical leading)"
        elif leadership_score <= -2:
            return "RISK OFF", f"Leadership score {leadership_score} ≤ -2 = RISK OFF (defensive leading)"
        else:
            return "NEUTRAL", f"Leadership score {leadership_score} in neutral range (-2 to +2) = NEUTRAL"
    
    def _get_fallback_sector_analysis(self) -> Dict:
        """Return fallback sector analysis"""
        return {
            'error': 'Sector analysis error',
            'total_points': 0.0,
            'leadership_score': 0.0,
            'rotation_signal': 'NEUTRAL',
            'points_breakdown': {
                'total_weighted_points': 0.0,
                'leadership_calculation': 'Using proxy estimates',
                'rotation_logic': 'Neutral due to data limitations'
            }
        }
