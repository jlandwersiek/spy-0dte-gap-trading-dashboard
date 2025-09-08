"""Trend analysis with EMA momentum and shift detection"""
from typing import Dict
import pandas as pd
from config import MOMENTUM_THRESHOLDS

class TrendAnalyzer:
    """Enhanced trend analysis with momentum shift detection"""
    
    def __init__(self):
        self.thresholds = MOMENTUM_THRESHOLDS
    
    def calculate_trend_momentum(self, hist_data: pd.DataFrame) -> Dict:
        """Calculate EMA-based trend momentum"""
        if hist_data is None or hist_data.empty or len(hist_data) < 20:
            return {
                'ema_separation': 0, 
                'price_vs_ema9': 0, 
                'trend_acceleration': 0, 
                'trend_strength': 0,
                'ema9_current': 0,
                'ema20_current': 0
            }
        
        # Calculate EMAs
        ema_9 = hist_data['Close'].ewm(span=9).mean()
        ema_20 = hist_data['Close'].ewm(span=20).mean()
        
        # Current values
        current_price = hist_data['Close'].iloc[-1]
        ema9_current = ema_9.iloc[-1]
        ema20_current = ema_20.iloc[-1]
        
        # EMA separation (trend strength)
        ema_separation = ((ema9_current - ema20_current) / ema20_current) * 100
        
        # Price vs EMA momentum
        price_vs_ema9 = ((current_price - ema9_current) / ema9_current) * 100
        
        # Rate of change in trend
        if len(ema_9) >= 5:
            ema9_roc = ((ema9_current - ema_9.iloc[-5]) / ema_9.iloc[-5]) * 100
            trend_acceleration = ema9_roc
        else:
            trend_acceleration = 0
        
        return {
            'ema_separation': ema_separation,
            'price_vs_ema9': price_vs_ema9,
            'trend_acceleration': trend_acceleration,
            'trend_strength': abs(ema_separation),
            'ema9_current': ema9_current,
            'ema20_current': ema20_current
        }
    
    def detect_momentum_shifts(self, hist_data: pd.DataFrame) -> Dict:
        """Detect rapid momentum changes in real-time"""
        if hist_data is None or hist_data.empty or len(hist_data) < 10:
            return {
                'shift_detected': False, 
                'shift_points': 0, 
                'momentum_5min': 0, 
                'momentum_10min': 0, 
                'volume_acceleration': 1.0,
                'momentum_divergence': 0
            }
        
        # Get recent price action
        recent_closes = hist_data['Close'].tail(10)
        recent_volumes = hist_data['Volume'].tail(10)
        
        # Calculate 5-minute momentum vs 10-minute momentum
        momentum_5min = ((recent_closes.iloc[-1] - recent_closes.iloc[-5]) / recent_closes.iloc[-5]) * 100
        momentum_10min = ((recent_closes.iloc[-1] - recent_closes.iloc[-10]) / recent_closes.iloc[-10]) * 100
        
        # Volume acceleration
        recent_vol_avg = recent_volumes.tail(5).mean()
        earlier_vol_avg = recent_volumes.head(5).mean()
        volume_acceleration = recent_vol_avg / earlier_vol_avg if earlier_vol_avg > 0 else 1
        
        # Detect momentum shift
        momentum_divergence = abs(momentum_5min - momentum_10min)
        
        shift_points = 0
        shift_detected = False
        
        # Strong momentum shift with volume confirmation
        if (momentum_divergence > self.thresholds['strong_divergence'] and 
            volume_acceleration > self.thresholds['strong_volume']):
            shift_points = 2.0 if momentum_5min > momentum_10min else -2.0
            shift_detected = True
        elif (momentum_divergence > self.thresholds['moderate_divergence'] and 
              volume_acceleration > self.thresholds['moderate_volume']):
            shift_points = 1.0 if momentum_5min > momentum_10min else -1.0
            shift_detected = True
        
        return {
            'shift_detected': shift_detected,
            'shift_points': shift_points,
            'momentum_5min': momentum_5min,
            'momentum_10min': momentum_10min,
            'volume_acceleration': volume_acceleration,
            'momentum_divergence': momentum_divergence
        }
    
    def analyze_vwap_dynamic(self, vwap_distance_pct: float, trend_data: Dict) -> Dict:
        """Dynamic VWAP analysis based on trend strength"""
        base_threshold = 0.15
        trend_strength = trend_data.get('trend_strength', 0)
        
        # In strong trends, lower the VWAP threshold (more sensitive)
        if trend_strength > 0.2:
            threshold_multiplier = 0.6  # 40% lower threshold
            regime = "STRONG TREND"
        elif trend_strength > 0.1:
            threshold_multiplier = 0.8  # 20% lower threshold
            regime = "MODERATE TREND"
        else:
            threshold_multiplier = 1.0  # Normal threshold
            regime = "RANGING"
        
        adjusted_threshold = base_threshold * threshold_multiplier
        
        # Points calculation
        if abs(vwap_distance_pct) > adjusted_threshold * 2:
            vwap_points = 2.0 if vwap_distance_pct > 0 else -2.0
            signal_strength = "STRONG"
        elif abs(vwap_distance_pct) > adjusted_threshold:
            vwap_points = 1.0 if vwap_distance_pct > 0 else -1.0
            signal_strength = "MODERATE"
        else:
            vwap_points = 0.0
            signal_strength = "NEUTRAL"
        
        return {
            'points': vwap_points,
            'signal_strength': signal_strength,
            'adjusted_threshold': adjusted_threshold,
            'trend_adjusted': trend_strength > 0.1,
            'regime': regime,
            'threshold_multiplier': threshold_multiplier
        }
