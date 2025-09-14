"""Main Streamlit application - Enhanced with Premium Analysis"""
import streamlit as st
from datetime import datetime, time
import streamlit.components.v1 as components

# Import our API clients
from api.tradier_client import TradierAPI

# Import our analyzers  
from analyzers.gap_analyzer import GapAnalyzer
from analyzers.sector_analyzer import SectorAnalyzer
from analyzers.internals_analyzer import InternalsAnalyzer
from analyzers.technical_analyzer import TechnicalAnalyzer
from analyzers.premium_analyzer import PremiumAnalyzer

# Import our signal generators
from signals.entry_signals import EntrySignalGenerator
from signals.exit_signals import ExitSignalManager

# Import our UI components
from ui.components import (
    display_data_sources_info, 
    display_main_decision, 
    display_header_info,
    display_price_targets, 
    display_market_analysis_details, 
    display_final_recommendation
)
from ui.breakdown_display import display_points_breakdown_ui
from ui.exit_dashboard import display_exit_signals_ui

# Import alert system
from utils.alert_system import AlertSystem, setup_alert_ui

# Import config
from config import MIAMI_TZ

# Page configuration
st.set_page_config(
    page_title="SPY 0DTE Gap Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_trading_window_status():
    """Get current trading window status with breadth reliability weighting"""
    current_time = datetime.now().time()
    
    # Your dad's observations about breadth reliability - now just for weighting
    if time(9, 45) <= current_time <= time(10, 30):
        return {
            'status': 'OPEN - CAUTION',
            'reliability': 'LOW',
            'message': 'Opening imbalances may reduce breadth signal reliability. Use price action confirmation.',
            'breadth_weight': 0.3,  # Reduce breadth influence
            'color': 'warning',
            'timing_warning': 'CAUTION: Opening volatility period - breadth signals less reliable'
        }
    elif time(10, 30) <= current_time <= time(11, 0):
        return {
            'status': 'OPTIMAL WINDOW',
            'reliability': 'HIGH', 
            'message': 'Peak breadth reliability window. Full signal confidence.',
            'breadth_weight': 1.0,  # Full breadth weight
            'color': 'success',
            'timing_warning': None
        }
    elif time(11, 0) <= current_time <= time(11, 30):
        return {
            'status': 'POST-OPTIMAL',
            'reliability': 'MEDIUM',
            'message': 'Past optimal window but signals still valid with reduced gap edge.',
            'breadth_weight': 0.8,
            'color': 'info', 
            'timing_warning': 'INFO: Past optimal window - gap edge diminishing'
        }
    elif time(13, 30) <= current_time <= time(14, 0):
        return {
            'status': 'PIVOT WATCH', 
            'reliability': 'MEDIUM',
            'message': 'Historical breadth pivot zone. Monitor for afternoon reversal patterns.',
            'breadth_weight': 0.7,
            'color': 'info',
            'timing_warning': 'PIVOT ZONE: Watch for potential afternoon reversals'
        }
    elif time(14, 30) <= current_time <= time(16, 0):
        return {
            'status': 'DANGER ZONE',
            'reliability': 'LOW', 
            'message': 'Extreme theta burn period for 0DTE options. High risk.',
            'breadth_weight': 0.5,
            'color': 'warning',
            'timing_warning': 'WARNING: Extreme theta burn - 0DTE options very risky'
        }
    elif time(9, 30) <= current_time <= time(9, 45):
        return {
            'status': 'OPENING BELL',
            'reliability': 'LOW',
            'message': 'Market opening - wait for initial volatility to settle.',
            'breadth_weight': 0.2,
            'color': 'warning', 
            'timing_warning': 'OPENING: High volatility - wait for settlement'
        }
    elif current_time >= time(16, 0) or current_time <= time(9, 30):
        return {
            'status': 'MARKET CLOSED',
            'reliability': 'ANALYSIS ONLY',
            'message': 'Market closed - analysis for planning only.',
            'breadth_weight': 1.0,  # Use full historical analysis
            'color': 'info',
            'timing_warning': 'MARKET CLOSED: Analysis for planning only'
        }
    else:
        return {
            'status': 'LUNCH HOURS',
            'reliability': 'LOW',
            'message': 'Low volume lunch period - reduced signal reliability.',
            'breadth_weight': 0.6,
            'color': 'info',
            'timing_warning': 'LUNCH PERIOD: Low volume may reduce signal quality'
        }

def display_premium_efficiency_panel(api):
    """Display the premium efficiency panel with clear data source labeling"""
    st.subheader("🎯 Premium Efficiency Analysis")
    
    premium_analyzer = PremiumAnalyzer(api.token)
    
    with st.spinner("Analyzing current option premiums..."):
        efficiency_data = premium_analyzer.get_premium_efficiency_data("SPY")
    
    if not efficiency_data:
        st.error("❌ **Unable to fetch live options data**")
        st.warning("⚠️ Your Tradier API token may not have access to real-time options chains")
        return
    
    # Show data source clearly
    st.success("✅ **LIVE OPTIONS DATA** - Real-time from Tradier API")
    
    current_price = efficiency_data['current_price']
    
    # Main metrics display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Current SPY Price", 
            value=f"${current_price:.2f}",
            help="Real-time price from Tradier API"
        )
    
    # Call analysis
    if efficiency_data['call_analysis']:
        call_data = efficiency_data['call_analysis']
        with col2:
            st.metric(
                label=f"Call ${call_data['strike']:.0f} Breakeven",
                value=f"{call_data['percentage_move_needed']:+.2f}%",
                delta=f"Premium: ${call_data['premium']:.2f}",
                help="Live options data from Tradier API"
            )
    
    # Put analysis  
    if efficiency_data['put_analysis']:
        put_data = efficiency_data['put_analysis']
        with col3:
            st.metric(
                label=f"Put ${put_data['strike']:.0f} Breakeven",
                value=f"{put_data['percentage_move_needed']:+.2f}%",
                delta=f"Premium: ${put_data['premium']:.2f}",
                help="Live options data from Tradier API"
            )
    
    # Detailed analysis in expander
    with st.expander("📊 Detailed Premium Breakdown"):
        st.info("📊 **Data Source: Live Tradier API options chains**")
        
        if efficiency_data['call_analysis']:
            call_data = efficiency_data['call_analysis']
            st.write("**Call Option:**")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Strike: ${call_data['strike']:.2f}")
                st.write(f"Premium: ${call_data['premium']:.2f}")
                st.write(f"Breakeven: ${call_data['breakeven_price']:.2f}")
            with col2:
                st.write(f"Move Needed: {call_data['percentage_move_needed']:+.2f}%")
                st.write(f"Bid-Ask Spread: ${call_data['bid_ask_spread']:.2f}")
                
                # Assessment
                move_needed = abs(call_data['percentage_move_needed'])
                if move_needed <= 0.33:
                    st.success("🟢 Reasonable move required")
                elif move_needed <= 0.67:
                    st.warning("🟡 Moderate move required")
                else:
                    st.error("🔴 Large move required")
        
        if efficiency_data['put_analysis']:
            put_data = efficiency_data['put_analysis'] 
            st.write("**Put Option:**")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Strike: ${put_data['strike']:.2f}")
                st.write(f"Premium: ${put_data['premium']:.2f}")
                st.write(f"Breakeven: ${put_data['breakeven_price']:.2f}")
            with col2:
                st.write(f"Move Needed: {put_data['percentage_move_needed']:+.2f}%")
                st.write(f"Bid-Ask Spread: ${put_data['bid_ask_spread']:.2f}")
                
                # Assessment
                move_needed = abs(put_data['percentage_move_needed'])
                if move_needed <= 0.33:
                    st.success("🟢 Reasonable move required")
                elif move_needed <= 0.67:
                    st.warning("🟡 Moderate move required")
                else:
                    st.error("🔴 Large move required")

def display_historical_analysis(api):
    """Display historical 2-4 PM analysis - REAL DATA ONLY"""
    st.subheader("📈 Historical 2-4 PM Performance Analysis")
    
    premium_analyzer = PremiumAnalyzer(api.token)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        days_back = st.selectbox("Analysis Period", [30, 60, 90], index=0)
    with col2:
        analyze_button = st.button("Analyze Historical Returns", type="primary")
    
    if analyze_button:
        with st.spinner(f"Analyzing last {days_back} days of 2-4 PM performance..."):
            analysis = premium_analyzer.analyze_historical_2pm_4pm_returns("SPY", days_back)
        
        if analysis:
            # Show real data analysis
            data_source = analysis.get('data_source', 'Unknown Source')
            
            if 'Yahoo Finance' in data_source:
                st.warning(f"⚠️ **FALLBACK DATA SOURCE** - {data_source}")
                st.info("Using Yahoo Finance data as Tradier API intraday history was unavailable.")
            else:
                st.success(f"✅ **LIVE DATA SOURCE** - {data_source}")
            
            # Display results
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Win Rate", f"{analysis['win_rate']:.1f}%")
            with col2:
                st.metric("Avg Return", f"{analysis['avg_daily_return']:.2f}%")
            with col3:
                st.metric("Avg Up Day", f"{analysis['avg_up_day_return']:.2f}%")
            with col4:
                st.metric("Avg Down Day", f"{analysis['avg_down_day_return']:.2f}%")
            
            # Analysis insights
            st.info(f"""
            **Key Insights for Premium Efficiency:**
            - **{analysis['up_days']} up days** averaging **{analysis['avg_up_day_return']:.2f}%**
            - **{analysis['down_days']} down days** averaging **{analysis['avg_down_day_return']:.2f}%**
            - **Average absolute move: {analysis.get('avg_abs_return', abs(analysis['avg_daily_return'])):.2f}%**
            - **Standard deviation: {analysis['std_deviation']:.2f}%**
            
            **Premium Rule of Thumb:** If typical premium is around {analysis.get('avg_abs_return', abs(analysis['avg_daily_return']))/3:.2f}%, 
            you need the market to move more than {analysis.get('avg_abs_return', abs(analysis['avg_daily_return'])):.2f}% to be profitable.
            """)
            
            # Recent performance table
            st.write("**Recent Daily Performance:**")
            display_df = analysis['raw_data'][['date', 'return_pct', 'direction']].copy()
            display_df['return_pct'] = display_df['return_pct'].round(2)
            st.dataframe(display_df, use_container_width=True)
            
        else:
            # Clear explanation when no data is available
            st.error("❌ **Historical Data Unavailable**")
            
            with st.expander("🔍 Why This Feature Isn't Working", expanded=True):
                st.markdown("""
                **The historical 2-4 PM analysis requires intraday data that your current setup cannot access:**
                
                **Likely Issues:**
                1. **Tradier API Token** - Your token may not have access to detailed historical intraday data
                2. **Account Type** - Free/basic Tradier accounts often lack intraday historical access  
                3. **Yahoo Finance Limitations** - Even the Yahoo fallback couldn't retrieve 15-minute SPY data
                
                **Solutions to Get Real Data:**
                1. **Upgrade Tradier Account** - Contact Tradier about intraday historical data access
                2. **Interactive Brokers** - IBKR accounts with $10K+ get full historical data via API
                3. **Polygon.io** - Professional data service ($99/month) with complete intraday history
                4. **Alpha Vantage** - Alternative API with historical intraday data
                
                **This feature will work once you have access to real intraday historical data.**
                """)
            
            # Suggest testing current API access
            if st.button("🧪 Test Current API Access"):
                with st.spinner("Testing your API capabilities..."):
                    # Test basic quote access
                    spy_quote = premium_analyzer.get_stock_quote("SPY")
                    if spy_quote:
                        st.success("✅ Your API can access current quotes")
                    else:
                        st.error("❌ Your API cannot access basic quotes")
                    
                    # Test option chain access  
                    option_data = premium_analyzer.get_option_chain("SPY")
                    if option_data:
                        st.success("✅ Your API can access options data")
                    else:
                        st.error("❌ Your API cannot access options data")
                    
                    st.info("Historical intraday data requires higher-tier API access than basic quotes/options.")

def main():
    st.title("📈 SPY 0DTE Gap Trading Dashboard")
    st.markdown("*Enhanced with Premium Analysis + Trend Sensitivity + Exit Signals + Smart Alerts*")
    
    # Add safety disclaimer
    with st.expander("⚠️ Important Disclaimer", expanded=False):
        st.warning("""
        **FINANCIAL DISCLAIMER:**
        - This dashboard is for educational and informational purposes only
        - Market internals use proxy calculations when real breadth data is unavailable
        - All proxy data is clearly labeled - verify critical information with your broker
        - 0DTE options trading involves significant risk and may not be suitable for all investors
        - Past performance (real or calculated) does not guarantee future results
        """)
    
    # Initialize session state
    if 'active_trade' not in st.session_state:
        st.session_state['active_trade'] = None
    if 'trade_history' not in st.session_state:
        st.session_state['trade_history'] = []
    
    # Show data sources info
    display_data_sources_info()
    
    # Sidebar configuration
    api_token, sandbox_mode, auto_refresh, trade_method, alert_settings = setup_sidebar()
    
    if not api_token:
        show_api_setup_instructions()
        return
    
    # Initialize components
    api = TradierAPI(api_token, sandbox_mode)
    entry_generator = EntrySignalGenerator()
    exit_manager = ExitSignalManager(api)
    
    # Initialize analyzers
    gap_analyzer = GapAnalyzer(api)
    sector_analyzer = SectorAnalyzer(api)
    internals_analyzer = InternalsAnalyzer(api)
    technical_analyzer = TechnicalAnalyzer(api)
    
    # Get current market data
    current_spy, price_source = get_current_spy_price(api)
    
    # Get trading window info (for weighting and warnings, not gating)
    window_info = get_trading_window_status()
    
    # Display enhanced header info with timing warnings
    display_enhanced_header_info(current_spy, price_source, window_info, sandbox_mode)
    
    # Auto-refresh logic
    handle_auto_refresh(auto_refresh, window_info['status'])
    
    # Premium efficiency panel (always show)
    st.markdown("---")
    display_premium_efficiency_panel(api)
    
    # ALWAYS show analysis and trading signals with timing warnings
    with st.spinner("🔍 Analyzing market conditions..."):
        analysis = get_market_analysis(
            gap_analyzer, sector_analyzer, internals_analyzer, 
            technical_analyzer, entry_generator, window_info
        )
        
        # Calculate price targets
        price_targets = calculate_price_targets(analysis, current_spy)
    
    # Check for alerts AFTER getting analysis
    if alert_settings.get('enabled', False):
        alert_system = AlertSystem()
        alert_system.check_and_send_alerts(analysis)
        
        # Also check exit safety alerts
        alert_system.check_exit_alerts()
    
    st.markdown("---")
    
    # Show timing warning if present (instead of disabling signals)
    if window_info.get('timing_warning'):
        if window_info['color'] == 'warning':
            st.warning(f"⚠️ **TIMING WARNING:** {window_info['timing_warning']}")
        elif window_info['color'] == 'info':
            st.info(f"ℹ️ **TIMING INFO:** {window_info['timing_warning']}")
        else:
            st.success(f"✅ **OPTIMAL TIMING:** {window_info['message']}")
    
    # Display main decision (always shown)
    display_main_decision(analysis)
    
    # Display price targets
    display_price_targets(current_spy, price_targets)
    
    # Display options suggestions if needed
    if trade_method == "Options Contracts":
        display_options_suggestions(price_targets)
    
    # Display analysis breakdown
    display_points_breakdown_ui(analysis)
    
    # Display market analysis details
    display_market_analysis_details(analysis)
    
    # Exit signals dashboard
    display_exit_signals_ui(exit_manager, st.session_state.get('active_trade'))
    
    # Final recommendation (with timing context)
    display_final_recommendation(analysis, window_info)
    
    # Historical analysis (always available)
    st.markdown("---")
    display_historical_analysis(api)
    
    # Footer
    display_footer(sandbox_mode)

def display_enhanced_header_info(current_spy, price_source, window_info, sandbox_mode):
    """Enhanced header with timing info (not gating signals)"""
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.metric(
            label="Current SPY Price", 
            value=f"${current_spy:.2f}",
            delta=f"Source: {price_source}"
        )
    
    with col2:
        st.metric(
            label="Trading Window", 
            value=window_info['status'],
            delta=f"Breadth Reliability: {window_info['reliability']}"
        )
    
    with col3:
        if sandbox_mode:
            st.warning("🧪 SANDBOX")
        else:
            st.success("📊 LIVE")
    
    # Show breadth weight impact if significant
    if window_info['breadth_weight'] < 0.8:
        st.caption(f"📊 Breadth signals weighted to {window_info['breadth_weight']*100:.0f}% due to time-of-day reliability")

def display_final_recommendation(analysis, window_info):
    """Display final trading recommendation with timing context"""
    st.header("🎯 Final Trading Recommendation")
    
    decision = analysis['decision']
    
    if decision != 'NO TRADE':
        # Show the signal with timing context
        if window_info.get('timing_warning'):
            st.success(f"✅ **SIGNAL: {decision}**")
            if window_info['color'] == 'warning':
                st.warning(f"⚠️ **EXECUTION CAUTION:** {window_info['timing_warning']}")
            elif window_info['status'] == 'MARKET CLOSED':
                st.info(f"📋 **PLAN FOR TOMORROW:** {window_info['timing_warning']}")
            else:
                st.info(f"ℹ️ **TIMING NOTE:** {window_info['timing_warning']}")
        else:
            st.success(f"✅ **EXECUTE TRADE: {decision}** - Optimal timing window")
        
        # Signal breakdown
        st.info(f"""
        **Signal Breakdown:**
        • Gap Analysis: {analysis['gap_analysis'].get('total_points', 0):.1f} points
        • Market Internals: {analysis['internals'].get('total_points', 0):.1f} points (weighted {window_info['breadth_weight']*100:.0f}%)
        • Sector Leadership: {analysis['sectors_enhanced'].get('total_points', 0):.1f} points
        • Technical Analysis: {analysis['technicals_enhanced'].get('total_points', 0):.1f} points
        • Trend Analysis: {analysis.get('decision_breakdown', {}).get('trend_contribution', 0):.1f} points
        """)
        
    else:
        st.error("❌ **NO TRADE** - Insufficient signals or unfavorable conditions")
        if window_info['status'] != 'MARKET CLOSED':
            st.info("Wait for stronger signals or better timing window.")

def handle_auto_refresh(auto_refresh, window_status):
    """Handle auto-refresh logic based on market status"""
    if auto_refresh:
        if window_status in ['MARKET CLOSED', 'LUNCH HOURS']:
            st.info("ℹ️ Auto-refresh paused during low-activity periods")
            if st.button("🔄 Manual Refresh", type="secondary"):
                st.rerun()
        else:
            # Auto-refresh during active market hours
            components.html("""
            <script>
            setTimeout(function() {
                window.parent.location.reload();
            }, 30000);
            </script>
            """, height=0)
            st.info("🔄 Auto-refreshing every 30 seconds during active market hours")
    
    # Manual refresh option always available
    if not auto_refresh:
        if st.button("🔄 Manual Refresh", type="secondary"):
            st.rerun()

def setup_sidebar():
    """Setup sidebar configuration with alert system"""
    with st.sidebar:
        st.header("⚙️ API Configuration")
        
        api_token = st.text_input(
            "Tradier API Token",
            type="password",
            help="Enter your Tradier API token (Production API for real data)"
        )
        
        sandbox_mode = False  # Always use production
        
        if api_token:
            api = TradierAPI(api_token, sandbox_mode)
            connection_ok, connection_msg = api.test_connection()
            if connection_ok:
                st.success(connection_msg)
            else:
                st.error(connection_msg)
        
        st.markdown("---")
        st.header("🔄 Refresh Settings")
        
        auto_refresh = st.checkbox("Auto Refresh (30s)", value=False)
        
        trade_method = st.radio(
            "Trading Method:",
            ["Options Contracts", "Stock/ETF"]
        )
        
        # Setup alert UI
        alert_settings = setup_alert_ui()
        
        st.markdown("---")
        if st.button("🔄 Refresh Data", type="primary"):
            st.rerun()
    
    return api_token, sandbox_mode, auto_refresh, trade_method, alert_settings

def show_api_setup_instructions():
    """Show API setup instructions"""
    st.warning("⚠️ Please enter your Tradier API token in the sidebar to continue.")
    st.info("""
    **How to get your Tradier API Token:**
    1. Sign up at [Tradier](https://tradier.com)
    2. Go to Account Settings → API Access
    3. Generate a new API token
    4. **Important**: Use Production API (not Sandbox) for real market data
    5. Enter the token in the sidebar
    """)

def get_current_spy_price(api):
    """Get current SPY price with fallbacks"""
    try:
        spy_quotes = api.get_quote('SPY')
        if spy_quotes and spy_quotes.get('last'):
            return float(spy_quotes['last']), "Tradier"
    except:
        pass
    
    try:
        from api.yahoo_client import get_cached_yahoo_data
        spy_data = get_cached_yahoo_data('SPY', '1d', '1m')
        if not spy_data.empty:
            return spy_data['Close'].iloc[-1], "Yahoo (Fallback)"
    except:
        pass
    
    return 640.27, "Static Fallback"

def get_market_analysis(gap_analyzer, sector_analyzer, internals_analyzer, 
                       technical_analyzer, entry_generator, window_info):
    """Get complete market analysis with breadth weighting"""
    # Get all analysis components
    gap_analysis = gap_analyzer.calculate_gap_analysis()
    internals = internals_analyzer.analyze_market_internals()
    sectors = sector_analyzer.analyze_sectors()
    technicals = technical_analyzer.analyze_technicals()
    spy_data = gap_analyzer.get_spy_data_enhanced()
    
    # Apply breadth weighting to internals analysis if it has breadth components
    if 'breadth_score' in internals:
        internals['original_breadth_score'] = internals['breadth_score']
        internals['breadth_score'] = internals['breadth_score'] * window_info['breadth_weight']
        internals['breadth_reliability'] = window_info['reliability']
    
    # Generate final decision with trend analysis and timing warnings
    analysis = entry_generator.get_final_decision(
        gap_analysis, internals, sectors, technicals, spy_data
    )
    
    # Add window info to analysis for display purposes
    analysis['window_info'] = window_info
    
    return analysis

def calculate_price_targets(analysis, current_spy):
    """Calculate price targets (simplified version)"""
    bullish_points = analysis['bullish_points']
    bearish_points = analysis['bearish_points']
    
    base_move = current_spy * 0.01  # 1% base move
    
    if bullish_points >= 8:
        upside_target = current_spy + (base_move * 1.4)
        downside_target = current_spy - (base_move * 0.6)
        upside_prob, downside_prob = 75, 25
        reasoning = ["Strong bullish signals suggest larger upside move"]
    elif bullish_points >= 6:
        upside_target = current_spy + (base_move * 1.1)
        downside_target = current_spy - (base_move * 0.7)
        upside_prob, downside_prob = 65, 35
        reasoning = ["Moderate bullish signals"]
    elif bearish_points >= 8:
        downside_target = current_spy - (base_move * 1.4)
        upside_target = current_spy + (base_move * 0.6)
        upside_prob, downside_prob = 25, 75
        reasoning = ["Strong bearish signals suggest larger downside move"]
    elif bearish_points >= 6:
        downside_target = current_spy - (base_move * 1.1)
        upside_target = current_spy + (base_move * 0.7)
        upside_prob, downside_prob = 35, 65
        reasoning = ["Moderate bearish signals"]
    else:
        upside_target = current_spy + (base_move * 0.8)
        downside_target = current_spy - (base_move * 0.8)
        upside_prob, downside_prob = 50, 50
        reasoning = ["Mixed signals - wider neutral range"]
    
    return {
        'upside_target': upside_target,
        'downside_target': downside_target,
        'upside_probability': upside_prob,
        'downside_probability': downside_prob,
        'reasoning': reasoning,
        'options_suggestions': {}
    }

def display_options_suggestions(price_targets):
    """Display options suggestions if available"""
    if price_targets.get('options_suggestions'):
        st.markdown("---")
        st.header("📋 Options Recommendations")
        st.warning("⚠️ **Using Theoretical Data - Live options unavailable in simplified version**")

def display_footer(sandbox_mode):
    """Display footer information"""
    current_time = datetime.now(MIAMI_TZ).strftime("%Y-%m-%d %H:%M:%S ET")
    st.markdown("---")
    st.caption(f"""
    Dashboard last updated: {current_time} | API Mode: {'Sandbox' if sandbox_mode else 'Production'} | 
    **Data Hierarchy:** Tradier PRIMARY → Yahoo FALLBACK → Static FALLBACK | Exit Signals Active | Smart Alerts + Exit Safety + Premium Analysis Enabled | 
    **⚠️ Market Internals use PROXY calculations - not real breadth data**
    """)

if __name__ == "__main__":
    main()
