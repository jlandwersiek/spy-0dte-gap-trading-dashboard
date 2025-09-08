"""Proxy data providers for fallback scenarios"""
from typing import Dict
from datetime import datetime

class ProxyDataProvider:
    """Provides reasonable proxy estimates when all APIs fail"""
    
    @staticmethod
    def get_spy_proxy_data(current_time: datetime) -> Dict:
        """Generate reasonable SPY proxy data"""
        hour = current_time.hour
        
        if hour < 9 or hour >= 16:
            return {
                'current_price': 640.27,
                'volume': 45000000,
                'gap_pct': -1.17,
                'source': 'Proxy (Market Closed)'
            }
        
        return {
            'current_price': 640.27 + (hour - 12) * 0.1,
            'volume': 50000000,
            'gap_pct': -1.17,
            'source': 'Proxy (Live Estimate)'
        }
    
    @staticmethod
    def get_sector_proxy_data() -> Dict:
        """Generate sector proxy data with realistic variations"""
        return {
            'XLK': {'change_pct': -1.01, 'volume_ratio': 1.5},
            'XLF': {'change_pct': -0.75, 'volume_ratio': 1.1}, 
            'XLV': {'change_pct': 0.10, 'volume_ratio': 1.0},
            'XLY': {'change_pct': -0.75, 'volume_ratio': 1.4},
            'XLI': {'change_pct': -0.96, 'volume_ratio': 0.9},
            'XLP': {'change_pct': -0.17, 'volume_ratio': 1.1},
            'XLE': {'change_pct': 0.15, 'volume_ratio': 0.7},
            'XLU': {'change_pct': -0.34, 'volume_ratio': 0.9},
            'XLRE': {'change_pct': -1.71, 'volume_ratio': 1.3}
        }
    
    @staticmethod
    def get_internals_proxy_data() -> Dict:
        """Generate market internals proxy based on sector sentiment"""
        sector_data = ProxyDataProvider.get_sector_proxy_data()
        positive_sectors = sum(1 for data in sector_data.values() if data['change_pct'] > 0)
        total_sectors = len(sector_data)
        
        breadth_ratio = positive_sectors / total_sectors
        
        return {
            'tick': {'value': ((breadth_ratio - 0.5) * 2000), 'signal': 'BEARISH' if breadth_ratio < 0.4 else 'NEUTRAL'},
            'trin': {'value': 1.0 / (0.8 + breadth_ratio * 0.4), 'signal': 'NEUTRAL'},
            'nyad': {'value': ((breadth_ratio - 0.5) * 4000), 'signal': 'BEARISH' if breadth_ratio < 0.4 else 'NEUTRAL'},
            'vold': {'value': 0.3 + breadth_ratio * 0.4, 'signal': 'BEARISH' if breadth_ratio < 0.4 else 'NEUTRAL'}
        }
