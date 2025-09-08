"""Exit signal management for 0DTE trades"""
from typing import Dict, Tuple
from datetime import datetime
import pytz

from config import MIAMI_TZ
from api.tradier_client import TradierAPI
from api.yahoo_client import get_cached_yahoo_data

class ExitSignalManager:
    """Dedicated exit signal management for 0DTE trades"""
    
    def __init__(self, api: TradierAPI):
        self.api = api
        self.miami_tz = MIAMI_TZ
    
    def get_current_option_price(self, strike: float, option_type: str, expiration: str = None) -> float:
        """Get current option price from Tradier"""
        try:
            if not expiration:
                expiration = datetime.now().strftime('%Y-%m-%d')
        
            options_data = self.api.get_options_chain('SPY', expiration)
        
            if not options_data or 'options' not in options_data:
                return None
            
            option_list = options_data['options'].get('option', [])
            if not option_list:
                return None
            
            if not isinstance(option_list, list):
                option_list = [option_list]
        
            # Find matching strike and type
            for option in option_list:
                if not option or not isinstance(option, dict):
                    continue
                
                if (float(option.get('strike', 0)) == strike and 
                    option.get('option_type') == option_type.lower()):
                
                    bid = float(option.get('bid', 0))
                    ask = float(option.get('ask', 0))
                
                    if bid > 0 and ask > 0:
                        return (bid + ask) / 2
                    elif option.get('last'):
                        return float(option.get('last', 0))
                        
            return None
        
        except Exception as e:
            return None
    
    def get_exit_signals(self, entry_decision: str, entry_price: float, entry_time: datetime, 
                        targets: Dict, trade_details: Dict = None) -> Dict:
        """Generate exit signals with correct P&L calculation"""
        
        current_time = datetime.now(self.miami_tz)
        
        exit_signals = {
            'primary_signal': 'HOLD',
            'urgency': 'LOW',
            'reasons': [],
            'profit_loss_pct': 0,
            'current_price': 0,
            'entry_price': entry_price,
            'time_warnings': [],
            'technical_exits': [],
            'should_exit': False,
            'exit_score': 0,
            'price_source': 'Unknown',
            'calculation_method': 'Unknown'
        }
        
        # Determine trade type and get appropriate current price
        trade_type = trade_details.get('trade_type', 'OPTIONS') if trade_details else 'OPTIONS'
        
        if trade_type == 'STOCK':
            current_price, price_source = self._get_current_spy_price()
            exit_signals['calculation_method'] = 'Stock Price Comparison'
            
        else:
            # For options trades, try to get actual option price
            strike = trade_details.get('strike') if trade_details else None
            option_type = 'put' if 'SHORT' in entry_decision else 'call'
            
            if strike:
                current_option_price = self.get_current_option_price(strike, option_type)
                
                if current_option_price:
                    current_price = current_option_price
                    price_source = 'Tradier Options'
                    exit_signals['calculation_method'] = 'Live Options Data'
                else:
                    current_price, price_source = self._estimate_option_value(
                        entry_price, entry_decision, entry_time, targets
                    )
                    exit_signals['calculation_method'] = 'Estimated Options Value'
            else:
                current_price, price_source = self._estimate_option_value(
                    entry_price, entry_decision, entry_time, targets
                )
                exit_signals['calculation_method'] = 'Estimated Options Value'
        
        exit_signals['current_price'] = current_price
        exit_signals['price_source'] = price_source
        
        # Calculate P&L correctly
        if current_price > 0:
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = -100
        
        exit_signals['profit_loss_pct'] = pnl_pct
        
        # TIME-BASED EXITS (Critical for 0DTE)
        market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
        minutes_to_close = (market_close - current_time).total_seconds() / 60
        
        exit_signals = self._analyze_time_exits(exit_signals, minutes_to_close)
        
        # PROFIT TARGET EXITS
        exit_signals = self._analyze_profit_exits(exit_signals, pnl_pct)
        
        # STOP LOSS EXITS
        exit_signals = self._analyze_stop_loss_exits(exit_signals, pnl_pct)
        
        # TARGET ACHIEVEMENT EXITS
        exit_signals = self._analyze_target_exits(exit_signals, entry_decision, targets)
        
        # FINAL EXIT DECISION
        exit_signals = self._make_final_exit_decision(exit_signals)
        
        return exit_signals
    
    def _analyze_time_exits(self, exit_signals: Dict, minutes_to_close: float) -> Dict:
        """Analyze time-based exit criteria"""
        if minutes_to_close <= 30:
            exit_signals['exit_score'] += 8
            exit_signals['primary_signal'] = 'IMMEDIATE EXIT'
            exit_signals['urgency'] = 'CRITICAL'
            exit_signals['time_warnings'].append("🚨 FINAL 30 MINUTES - Theta burn accelerating")
            
        elif minutes_to_close <= 60:
            exit_signals['exit_score'] += 5
            exit_signals['primary_signal'] = 'STRONG EXIT'
            exit_signals['urgency'] = 'HIGH'
            exit_signals['time_warnings'].append("⚠️ Final hour - Start looking for exit")
            
        elif minutes_to_close <= 90:
            exit_signals['exit_score'] += 3
            exit_signals['time_warnings'].append("🕐 90 minutes left - Prepare for exit")
        
        return exit_signals
    
    def _analyze_profit_exits(self, exit_signals: Dict, pnl_pct: float) -> Dict:
        """Analyze profit-based exit criteria"""
        if pnl_pct >= 100:
            exit_signals['exit_score'] += 6
            exit_signals['reasons'].append(f"🎯 MASSIVE WIN: {pnl_pct:.1f}% profit - Take it!")
            
        elif pnl_pct >= 50:
            exit_signals['exit_score'] += 4
            exit_signals['reasons'].append(f"✅ STRONG PROFIT: {pnl_pct:.1f}% - Consider taking profits")
            
        elif pnl_pct >= 25:
            exit_signals['exit_score'] += 2
            exit_signals['reasons'].append(f"💰 Good profit: {pnl_pct:.1f}% - Watch for reversal")
        
        return exit_signals
    
    def _analyze_stop_loss_exits(self, exit_signals: Dict, pnl_pct: float) -> Dict:
        """Analyze stop loss exit criteria"""
        if pnl_pct <= -70:
            exit_signals['exit_score'] += 8
            exit_signals['primary_signal'] = 'IMMEDIATE EXIT'
            exit_signals['urgency'] = 'CRITICAL'
            exit_signals['reasons'].append(f"🛑 MAJOR STOP LOSS: {pnl_pct:.1f}% loss")
            
        elif pnl_pct <= -50:
            exit_signals['exit_score'] += 6
            exit_signals['primary_signal'] = 'STRONG EXIT'
            exit_signals['urgency'] = 'HIGH'
            exit_signals['reasons'].append(f"🛑 STOP LOSS HIT: {pnl_pct:.1f}% loss")
            
        elif pnl_pct <= -30:
            exit_signals['exit_score'] += 4
            exit_signals['reasons'].append(f"⚠️ Significant loss: {pnl_pct:.1f}% - Consider exit")
        
        return exit_signals
    
    def _analyze_target_exits(self, exit_signals: Dict, entry_decision: str, targets: Dict) -> Dict:
        """Analyze target achievement exits"""
        upside_target = targets.get('upside_target', exit_signals['entry_price'] * 1.01)
        downside_target = targets.get('downside_target', exit_signals['entry_price'] * 0.99)
        
        spy_price, _ = self._get_current_spy_price()
        
        if 'LONG' in entry_decision and spy_price >= upside_target:
            exit_signals['exit_score'] += 5
            exit_signals['reasons'].append(f"🎯 SPY TARGET HIT: ${spy_price:.2f} >= ${upside_target:.2f}")
            
        elif 'SHORT' in entry_decision and spy_price <= downside_target:
            exit_signals['exit_score'] += 5
            exit_signals['reasons'].append(f"🎯 SPY TARGET HIT: ${spy_price:.2f} <= ${downside_target:.2f}")
        
        return exit_signals
    
    def _make_final_exit_decision(self, exit_signals: Dict) -> Dict:
        """Make final exit decision based on score"""
        if exit_signals['exit_score'] >= 8:
            exit_signals['should_exit'] = True
            exit_signals['primary_signal'] = 'IMMEDIATE EXIT'
            exit_signals['urgency'] = 'CRITICAL'
            exit_signals['exit_score'] = min(exit_signals['exit_score'], 10)
        elif exit_signals['exit_score'] >= 5:
            exit_signals['should_exit'] = True
            exit_signals['primary_signal'] = 'STRONG EXIT'
            exit_signals['urgency'] = 'HIGH'
        elif exit_signals['exit_score'] >= 3:
            exit_signals['primary_signal'] = 'CONSIDER EXIT'
            exit_signals['urgency'] = 'MEDIUM'
        
        return exit_signals
    
    def _get_current_spy_price(self) -> Tuple[float, str]:
        """Get current SPY stock price with proper fallback"""
        try:
            spy_quote = self.api.get_quote('SPY')
            if spy_quote and spy_quote.get('last'):
                return float(spy_quote['last']), 'Tradier'
        except:
            pass
        
        try:
            spy_data = get_cached_yahoo_data('SPY', '1d', '1m')
            if not spy_data.empty:
                return spy_data['Close'].iloc[-1], 'Yahoo (Fallback)'
        except:
            pass
        
        return 640.27, 'Static Fallback'
    
    def _estimate_option_value(self, entry_price: float, entry_decision: str, 
                              entry_time: datetime, targets: Dict) -> Tuple[float, str]:
        """Estimate current option value when live data unavailable"""
        try:
            current_time = datetime.now(self.miami_tz)
            spy_price, _ = self._get_current_spy_price()
            
            # Time decay factor
            time_in_trade = (current_time - entry_time).total_seconds() / 3600
            time_decay_factor = max(0.1, 1 - (time_in_trade * 0.15))
            
            # Moneyness factor
            if 'LONG' in entry_decision:
                upside_target = targets.get('upside_target', spy_price * 1.005)
                if spy_price >= upside_target:
                    intrinsic_multiplier = 2.5
                elif spy_price >= upside_target * 0.5:
                    intrinsic_multiplier = 1.2
                else:
                    intrinsic_multiplier = 0.6
            else:
                downside_target = targets.get('downside_target', spy_price * 0.995)
                if spy_price <= downside_target:
                    intrinsic_multiplier = 2.5
                elif spy_price <= downside_target * 1.5:
                    intrinsic_multiplier = 1.2
                else:
                    intrinsic_multiplier = 0.6
            
            estimated_value = entry_price * intrinsic_multiplier * time_decay_factor
            estimated_value = max(0.01, estimated_value)
            
            return estimated_value, 'Estimated'
            
        except:
            return entry_price * 0.5, 'Conservative Estimate'
