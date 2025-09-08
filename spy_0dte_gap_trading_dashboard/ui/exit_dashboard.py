"""Exit signals dashboard UI with URL persistence"""
import streamlit as st
import pytz
from datetime import datetime, timedelta
from typing import Dict
import urllib.parse
import base64
import json

def encode_trade_for_url(trade_data):
    """Encode trade data for URL storage"""
    try:
        # Convert datetime objects to strings
        trade_copy = trade_data.copy()
        trade_copy['entry_time'] = trade_data['entry_time'].isoformat()
        trade_copy['created_at'] = trade_data['created_at'].isoformat()
        
        # Convert to JSON and encode
        json_str = json.dumps(trade_copy)
        encoded = base64.b64encode(json_str.encode()).decode()
        return encoded
    except Exception as e:
        return None

def decode_trade_from_url(encoded_data):
    """Decode trade data from URL"""
    try:
        json_str = base64.b64decode(encoded_data).decode()
        trade_data = json.loads(json_str)
        
        # Convert strings back to datetime
        trade_data['entry_time'] = datetime.fromisoformat(trade_data['entry_time'])
        trade_data['created_at'] = datetime.fromisoformat(trade_data['created_at'])
        return trade_data
    except Exception as e:
        return None

def update_url_with_trade(trade_data):
    """Update URL with trade data"""
    try:
        encoded_trade = encode_trade_for_url(trade_data)
        if encoded_trade:
            st.query_params.trade = encoded_trade
    except Exception as e:
        pass  # Fail silently if URL update doesn't work

def clear_url_trade():
    """Clear trade from URL"""
    try:
        st.query_params.clear()
    except Exception as e:
        pass  # Fail silently if URL clear doesn't work

def display_exit_signals_ui(exit_manager, entry_data=None):
    """UI component for exit signals - PERSISTENT VERSION"""
    
    st.markdown("---")
    st.header("🚪 EXIT SIGNAL DASHBOARD")
    
    # Check URL for restored trade first
    try:
        if 'trade' in st.query_params and not st.session_state.get('active_trade'):
            restored_trade = decode_trade_from_url(st.query_params['trade'])
            if restored_trade:
                st.session_state['active_trade'] = restored_trade
                st.success("✅ Trade restored from previous session!")
    except Exception as e:
        pass  # Fail silently if URL restoration doesn't work
    
    # Get active trade from session state
    active_trade = st.session_state.get('active_trade')
    
    if not active_trade:
        _display_trade_entry_form()
    else:
        _display_active_trade_tracking(exit_manager, active_trade)
    
    # Trade management buttons
    if st.session_state.get('active_trade'):
        _display_trade_management_buttons()

def _display_trade_entry_form():
    """Display the trade entry form"""
    st.info("""
    **👋 No Active Position Detected**
    
    To get exit signals, you need to track your entry:
    • Entry time and price  
    • Direction (LONG/SHORT)
    • Trade type (Options/Stock)
    • Strike price (for options)
    
    *Use the form below to input your trade details*
    """)
    
    with st.form("persistent_trade_entry", clear_on_submit=False):
        st.subheader("📝 Enter Your Trade Details")
        
        col1, col2 = st.columns(2)
        with col1:
            entry_direction = st.selectbox(
                "Direction", 
                ["STRONG LONG", "MODERATE LONG", "STRONG SHORT", "MODERATE SHORT"],
                help="What the dashboard recommended when you entered"
            )
            
            trade_type = st.selectbox(
                "Trade Type", 
                ["OPTIONS", "STOCK"],
                help="Are you trading options contracts or actual SPY shares?"
            )
            
            entry_price = st.number_input(
                "Entry Price ($)", 
                value=0.00, 
                step=0.01, 
                format="%.3f",
                help="OPTIONS: Premium paid per contract (e.g., 0.19, 1.85). STOCK: Share price"
            )
            
        with col2:
            default_time = (datetime.now() - timedelta(hours=1)).time()
            entry_time_input = st.time_input(
                "Entry Time (EDT)", 
                value=default_time,
                help="When you actually executed the trade"
            )
            
            if trade_type == "OPTIONS":
                strike_price = st.number_input(
                    "Strike Price", 
                    value=640.0, 
                    step=1.0,
                    help="The strike of your calls/puts (find on broker confirmation)"
                )
            else:
                strike_price = None
        
        trade_notes = st.text_input(
            "Notes (Optional)", 
            placeholder="e.g., 10 contracts, scalp play, etc.",
            help="Any additional details about your trade"
        )
        
        # Form buttons
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("🎯 Start Exit Tracking", type="primary")
        with col2:
            if st.session_state.get('trade_history'):
                if st.form_submit_button("📜 Load Recent Trade"):
                    recent_trade = st.session_state['trade_history'][-1]
                    st.session_state['form_prefill'] = recent_trade
                    st.rerun()
        
        # Handle form submission
        if submitted:
            _handle_trade_submission(entry_direction, trade_type, entry_price, 
                                   entry_time_input, strike_price, trade_notes)

def _handle_trade_submission(entry_direction, trade_type, entry_price, 
                           entry_time_input, strike_price, trade_notes):
    """Handle trade form submission with URL persistence"""
    if entry_price <= 0:
        st.error("⚠️ Entry price must be greater than 0")
    elif trade_type == "OPTIONS" and (not strike_price or strike_price <= 0):
        st.error("⚠️ Strike price required for options trades")
    else:
        # Create trade record
        today = datetime.now(pytz.timezone('US/Eastern')).date()
        entry_datetime = datetime.combine(today, entry_time_input).replace(tzinfo=pytz.timezone('US/Eastern'))
        
        trade_record = {
            'entry_decision': entry_direction,
            'entry_price': entry_price,
            'entry_time': entry_datetime,
            'trade_type': trade_type,
            'strike': strike_price,
            'notes': trade_notes,
            'created_at': datetime.now(),
            'targets': {
                'upside_target': 0,
                'downside_target': 0
            }
        }
        
        # Save to session state AND URL
        st.session_state['active_trade'] = trade_record
        update_url_with_trade(trade_record)
        
        # Add to history
        if 'trade_history' not in st.session_state:
            st.session_state['trade_history'] = []
        st.session_state['trade_history'].append(trade_record)
        
        # Keep only last 10 trades in history
        st.session_state['trade_history'] = st.session_state['trade_history'][-10:]
        
        st.success("✅ Trade tracking started! This will persist across page refreshes.")
        st.rerun()

def _display_active_trade_tracking(exit_manager, active_trade):
    """Display active trade with exit signals"""
    st.success(f"📊 **Active Trade Tracking** (Started: {active_trade['created_at'].strftime('%H:%M:%S')})")
    
    try:
        trade_details = {
            'trade_type': active_trade.get('trade_type', 'OPTIONS'),
            'strike': active_trade.get('strike')
        }
        
        exit_signals = exit_manager.get_exit_signals(
            active_trade['entry_decision'],
            active_trade['entry_price'], 
            active_trade['entry_time'],
            active_trade['targets'],
            trade_details
        )
        
        # Store current P&L for exit alerts
        st.session_state['current_trade_pnl'] = exit_signals.get('profit_loss_pct', 0)
        
        # Main exit signal display
        signal_color = {
            'IMMEDIATE EXIT': '#dc3545',
            'STRONG EXIT': '#fd7e14',
            'CONSIDER EXIT': '#ffc107',
            'HOLD': '#28a745'
        }.get(exit_signals['primary_signal'], '#6c757d')
        
        st.markdown(f"""
        <div style="text-align: center; padding: 25px; background: {signal_color}20; 
                    border: 3px solid {signal_color}; border-radius: 15px; margin: 20px 0;">
            <h1 style="color: {signal_color}; margin: 0;">
                {'🚨' if exit_signals['should_exit'] else '✋' if exit_signals['primary_signal'] == 'CONSIDER EXIT' else '✅'}
            </h1>
            <h2 style="color: {signal_color}; margin: 10px 0;">{exit_signals['primary_signal']}</h2>
            <h3 style="margin: 10px 0;">Urgency: {exit_signals['urgency']}</h3>
            <p style="font-size: 1.5em; margin: 15px 0;">
                <strong>P&L: {exit_signals['profit_loss_pct']:+.1f}%</strong>
            </p>
            <p style="font-size: 0.9em; margin: 5px 0; opacity: 0.8;">
                {exit_signals['calculation_method']} | {exit_signals['price_source']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Trade details and P&L
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Entry Price", f"${exit_signals['entry_price']:.2f}")
            if trade_details['strike']:
                st.metric("Strike", f"${trade_details['strike']:.0f}")
            
        with col2:
            st.metric("Current Price", f"${exit_signals['current_price']:.2f}")
            st.metric("Trade Type", trade_details['trade_type'])
            
        with col3:
            pnl_delta = f"{exit_signals['profit_loss_pct']:+.1f}%"
            st.metric("Profit/Loss", pnl_delta)
            st.metric("Exit Score", f"{min(exit_signals['exit_score'], 10)}/10")
            
        with col4:
            time_in_trade = (datetime.now(pytz.timezone('US/Eastern')) - active_trade['entry_time']).total_seconds() / 3600
            st.metric("Time in Trade", f"{time_in_trade:.1f} hours")
            st.metric("Direction", active_trade['entry_decision'].replace('STRONG ', '').replace('MODERATE ', ''))
        
        # Notes if any
        if active_trade.get('notes'):
            st.info(f"📝 **Notes:** {active_trade['notes']}")
        
        # Data quality indicator
        if exit_signals['calculation_method'] == 'Live Options Data':
            st.success("✅ Using live options pricing data from Tradier")
        elif exit_signals['calculation_method'] == 'Estimated Options Value':
            st.warning("⚠️ Using estimated options value - check your broker for exact P&L")
        elif exit_signals['calculation_method'] == 'Stock Price Comparison':
            st.info("📊 Using live stock price")
        
        # Exit reasons
        if exit_signals['reasons']:
            st.subheader("📋 Exit Reasons:")
            for reason in exit_signals['reasons']:
                st.write(f"• {reason}")
        
        # Time warnings
        if exit_signals['time_warnings']:
            st.subheader("⏰ Time Warnings:")
            for warning in exit_signals['time_warnings']:
                st.warning(warning)
        
        # Technical exits
        if exit_signals['technical_exits']:
            st.subheader("📈 Technical Signals:")
            for signal in exit_signals['technical_exits']:
                st.write(f"• {signal}")
                
    except Exception as e:
        st.error(f"Error calculating exit signals: {str(e)}")
        st.write("**Debug info:**")
        st.write(f"Active trade: {active_trade}")

def _display_trade_management_buttons():
    """Display simplified trade management buttons"""
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Close Trade", type="primary", use_container_width=True):
            closed_trade = st.session_state['active_trade'].copy()
            closed_trade['closed_at'] = datetime.now()
            closed_trade['close_reason'] = 'CLOSED'
            
            st.session_state['active_trade'] = None
            clear_url_trade()
            st.success("Trade closed!")
            st.rerun()
            
    with col2:
        if st.button("🗑️ Clear Tracking", type="secondary", use_container_width=True):
            st.session_state['active_trade'] = None
            clear_url_trade()
            st.info("Trade tracking cleared.")
            st.rerun()
