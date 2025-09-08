"""Main Streamlit application - Simplified and Modular with Alert System"""
import streamlit as st
from datetime import datetime
import time
import streamlit.components.v1 as components

# Import our API clients
from api.tradier_client import TradierAPI

# Import our analyzers  
from analyzers.gap_analyzer import GapAnalyzer
from analyzers.sector_analyzer import SectorAnalyzer
from analyzers.internals_analyzer import InternalsAnalyzer
from analyzers.technical_analyzer import TechnicalAnalyzer

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

def main():
    st.title("📈 SPY 0DTE Gap Trading Dashboard")
    st.markdown("*Enhanced with Trend Sensitivity + Exit Signals + Smart Alerts*")
    
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
    trading_window_ok, window_message = gap_analyzer.check_trading_window()
    
    # Display header info
    display_header_info(current_spy, price_source, trading_window_ok, window_message, sandbox_mode)
    
    # Auto-refresh logic
    handle_auto_refresh(auto_refresh, trading_window_ok)
    
    # Get analysis
    with st.spinner("🔍 Analyzing market conditions..."):
        analysis = get_market_analysis(
            gap_analyzer, sector_analyzer, internals_analyzer, 
            technical_analyzer, entry_generator
        )
        
        # Calculate price targets
        price_targets = calculate_price_targets(analysis, current_spy)
    
    # Check for alerts AFTER getting analysis
    if alert_settings.get('enabled', False):
        alert_system = AlertSystem()
        alert_system.check_and_send_alerts(analysis)
        
        # Also check exit safety alerts
        alert_system.check_exit_alerts()
    
    # Display main decision
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
    
    # Final recommendation
    display_final_recommendation(analysis, trading_window_ok, window_message)
    
    # Footer
    display_footer(sandbox_mode)

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

def handle_auto_refresh(auto_refresh, trading_window_ok):
    """Handle auto-refresh logic - trades persist via URL so always safe"""
    if auto_refresh and trading_window_ok:
        # Use JavaScript to auto-refresh every 30 seconds during trading hours
        components.html("""
        <script>
        setTimeout(function() {
            window.parent.location.reload();
        }, 30000);
        </script>
        """, height=0)
        st.info("🔄 Auto-refreshing every 30 seconds during trading hours")
        
    elif auto_refresh and not trading_window_ok:
        st.info("ℹ️ Auto-refresh paused - Outside trading window")
        if st.button("🔄 Manual Refresh", type="secondary"):
            st.rerun()
    
    # Manual refresh option always available
    if not auto_refresh:
        if st.button("🔄 Manual Refresh", type="secondary"):
            st.rerun()

def get_market_analysis(gap_analyzer, sector_analyzer, internals_analyzer, 
                       technical_analyzer, entry_generator):
    """Get complete market analysis"""
    # Get all analysis components
    gap_analysis = gap_analyzer.calculate_gap_analysis()
    internals = internals_analyzer.analyze_market_internals()
    sectors = sector_analyzer.analyze_sectors()
    technicals = technical_analyzer.analyze_technicals()
    spy_data = gap_analyzer.get_spy_data_enhanced()
    
    # Generate final decision with trend analysis and timing warnings
    analysis = entry_generator.get_final_decision(
        gap_analysis, internals, sectors, technicals, spy_data
    )
    
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
    **Data Hierarchy:** Tradier PRIMARY → Yahoo FALLBACK → Static FALLBACK | Exit Signals Active | Smart Alerts + Exit Safety Enabled
    """)

if __name__ == "__main__":
    main()
