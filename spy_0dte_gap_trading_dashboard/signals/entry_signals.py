"""Enhanced entry signal generation with trend sensitivity and timing warnings"""
from typing import Dict
from config import DECISION_THRESHOLDS
from analyzers.trend_analyzer import TrendAnalyzer

class EntrySignalGenerator:
    """Enhanced entry signal generator with trend analysis and timing warnings"""
    
    def __init__(self):
        self.trend_analyzer = TrendAnalyzer()
        self.thresholds = DECISION_THRESHOLDS
    
    def get_final_decision(self, gap_analysis: Dict, internals: Dict, sectors: Dict, 
                          technicals: Dict, spy_data: Dict) -> Dict:
        """Generate final decision with time-based trading windows"""
        
        # ALWAYS calculate the points (for learning/analysis)
        bullish_points, bearish_points, decision_breakdown = self._calculate_points(
            gap_analysis, internals, sectors, technicals, spy_data
        )
        
        # Determine the signal strength (regardless of time)
        signal_decision, confidence = self._determine_signal_strength(bullish_points, bearish_points)
        
        # Check trading window
        from analyzers.gap_analyzer import GapAnalyzer
        gap_analyzer = GapAnalyzer(None)  # Just for window check
        trading_window_ok, window_message = gap_analyzer.check_trading_window()
        
        # Override decision if outside trading window
        if trading_window_ok and "PRIME 0DTE WINDOW" in window_message:
            # Within trading window - use calculated decision
            final_decision = signal_decision
            warning_message = None
        else:
            # Outside trading window - show analysis but warn against trading
            final_decision = "NO TRADE - OUTSIDE WINDOW"
            warning_message = self._get_timing_warning(signal_decision, window_message)
        
        return {
            'decision': final_decision,
            'confidence': confidence,
            'bullish_points': bullish_points,
            'bearish_points': bearish_points,
            'decision_breakdown': decision_breakdown,
            'raw_signal': signal_decision,  # What indicators actually say
            'trading_window_ok': trading_window_ok,
            'window_message': window_message,
            'timing_warning': warning_message,
            'gap_analysis': gap_analysis,
            'internals': internals,
            'sectors_enhanced': sectors,
            'technicals_enhanced': technicals,
            'trend_analysis': spy_data.get('trend_analysis', {}),
            'momentum_shift': spy_data.get('momentum_shift', {}),
            'dynamic_vwap': spy_data.get('dynamic_vwap', {}),
        }

    def _get_timing_warning(self, raw_signal: str, window_message: str) -> str:
        """Generate appropriate timing warning"""
        if "OPENING VOLATILITY" in window_message:
            return f"TIMING WARNING: Indicators show {raw_signal}, but opening volatility makes execution risky. Wait for 9:45 AM."
        elif "POST-WINDOW" in window_message:
            return f"TIMING WARNING: Indicators show {raw_signal}, but gap edge has diminished. Consider waiting for tomorrow."
        elif "LUNCH DOLDRUMS" in window_message:
            return f"TIMING WARNING: Indicators show {raw_signal}, but low volume makes fills poor. Avoid lunch hours."
        elif "DANGER ZONE" in window_message:
            return f"TIMING WARNING: Indicators show {raw_signal}, but theta burn is extreme. Exit existing positions only."
        elif "Weekend" in window_message:
            return f"ANALYSIS ONLY: Indicators would suggest {raw_signal} if market were open. Review for Monday."
        else:
            return f"TIMING WARNING: Indicators show {raw_signal}, but market timing is suboptimal."

    def _calculate_points(self, gap_analysis: Dict, internals: Dict, sectors: Dict, 
                         technicals: Dict, spy_data: Dict) -> tuple:
        """Calculate bullish/bearish points from all components"""
        # Get points from each component
        gap_points = gap_analysis.get('total_points', 0)
        internals_points = internals.get('total_points', 0)
        sectors_points = sectors.get('total_points', 0)
        technicals_points = technicals.get('total_points', 0)
        
        # Add trend analysis points if available
        trend_analysis = spy_data.get('trend_analysis', {})
        momentum_shift = spy_data.get('momentum_shift', {})
        
        trend_points = 0
        if trend_analysis:
            trend_points += trend_analysis.get('ema_points', 0)
            trend_points += trend_analysis.get('acceleration_points', 0)
        
        if momentum_shift and momentum_shift.get('shift_detected', False):
            trend_points += momentum_shift.get('shift_points', 0)
        
        # Calculate total bullish and bearish points
        total_bullish = (max(0, gap_points) + max(0, internals_points) + 
                        max(0, sectors_points) + max(0, technicals_points) + 
                        max(0, trend_points))
        
        total_bearish = (abs(min(0, gap_points)) + abs(min(0, internals_points)) + 
                        abs(min(0, sectors_points)) + abs(min(0, technicals_points)) + 
                        abs(min(0, trend_points)))
        
        decision_breakdown = {
            'gap_contribution': gap_points,
            'internals_contribution': internals_points,
            'sectors_contribution': sectors_points,
            'technicals_contribution': technicals_points,
            'trend_contribution': trend_points,
            'volatility_contribution': 0,  # Can add volatility analysis later
            'bullish_total': total_bullish,
            'bearish_total': total_bearish,
            'decision_logic': f"Bullish: {total_bullish:.1f} vs Bearish: {total_bearish:.1f}"
        }
        
        return total_bullish, total_bearish, decision_breakdown

    def _determine_signal_strength(self, bullish_points: float, bearish_points: float) -> tuple:
        """Determine signal strength from points"""
        net_points = bullish_points - bearish_points
        
        if net_points >= self.thresholds.get('strong_signal', 7):
            return "STRONG LONG", "HIGH"
        elif net_points >= self.thresholds.get('moderate_signal', 5):
            return "MODERATE LONG", "MEDIUM"
        elif net_points <= -self.thresholds.get('strong_signal', 7):
            return "STRONG SHORT", "HIGH"
        elif net_points <= -self.thresholds.get('moderate_signal', 5):
            return "MODERATE SHORT", "MEDIUM"
        else:
            return "NO TRADE", "LOW"
