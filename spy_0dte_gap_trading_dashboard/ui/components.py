"""Reusable UI components"""
import streamlit as st
from typing import Dict
from datetime import datetime
import pytz


def display_data_sources_info():
    """Show users what data comes from where"""
    with st.expander("📊 Data Sources & Reliability", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🔴 Tradier API (Primary)")
            st.markdown("""
            ✅ **Real-time SPY quotes**
            ✅ **Live sector ETF data** 
            ✅ **Historical OHLCV data**
            ✅ **Options chains with Greeks**
            ✅ **Volume & trading data**
            ✅ **Market hours status**
            
            *Most reliable for trading decisions*
            """)
        
        with col2:
            st.markdown("### 🟡 Yahoo Finance (Fallback)")
            st.markdown("""
            ⚠️ **Market internals proxies** (Tradier unavailable)
            ⚠️ **Backup price data** (if Tradier fails)
            ⚠️ **Historical data backup**
            
            ❌ **No real options data**
            ❌ **No real market internals**
            ❌ **Can be rate limited**
            
            *Used when Tradier unavailable*
            """)
        
        with col3:
            st.markdown("### 🟢 Proxy Estimates (Final Fallback)")
            st.markdown("""
            📊 **Reasonable market estimates**
            📊 **Based on typical conditions**
            📊 **Ensures system always works**
            📊 **Transparent about limitations**
            
            ✅ **Never fails completely**
            ✅ **Maintains functionality**
            
            *Used when all APIs fail*
            """)

def display_main_decision(analysis: Dict):
    """Display analysis with timing warnings"""
    raw_signal = analysis.get('raw_signal', analysis['decision'])
    final_decision = analysis['decision']
    timing_warning = analysis.get('timing_warning')
    
    # Show the raw signal analysis if different from final decision
    if raw_signal != final_decision and timing_warning:
        st.markdown("### 📊 Technical Analysis")
        st.info(f"**Indicators Suggest:** {raw_signal} (Confidence: {analysis['confidence']})")
        st.markdown(f"**Bullish Points:** {analysis['bullish_points']:.1f} | **Bearish Points:** {analysis['bearish_points']:.1f}")
        st.markdown("---")
    
    # Show the final decision with appropriate coloring
    if final_decision.startswith("NO TRADE - OUTSIDE"):
        decision_color = '⏰'
        decision_bg_color = '#fff3cd'  # Warning yellow
        border_color = '#ffc107'
        decision_display = "NO TRADE - OUTSIDE WINDOW"
    else:
        decision_color = {
            'STRONG LONG': '🟢', 'MODERATE LONG': '🟡', 
            'STRONG SHORT': '🔴', 'MODERATE SHORT': '🟠',
            'NO TRADE': '⚪'
        }.get(final_decision, '⚪')
        
        decision_bg_color = {
            'STRONG LONG': '#d4edda', 'MODERATE LONG': '#fff3cd', 
            'STRONG SHORT': '#f8d7da', 'MODERATE SHORT': '#ffeaa7',
            'NO TRADE': '#e2e3e5'
        }.get(final_decision, '#e2e3e5')
        
        border_color = '#007bff'
        decision_display = final_decision
    
    st.markdown(f"""
    <div style="text-align: center; padding: 30px; background: {decision_bg_color}; 
                border-radius: 15px; border: 3px solid {border_color}; margin: 20px 0;">
        <h1 style="margin: 0; font-size: 4em; color: #333;">{decision_color}</h1>
        <h2 style="margin: 10px 0; color: #333;">{decision_display}</h2>
        <h3 style="margin: 10px 0; color: #666;">Confidence: {analysis['confidence']}</h3>
        <p style="font-size: 1.3em; margin: 15px 0; color: #333;">
            <strong>Bullish Points: {analysis['bullish_points']:.1f} | Bearish Points: {analysis['bearish_points']:.1f}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show timing warning if present
    if timing_warning:
        if "DANGER ZONE" in timing_warning or "theta burn" in timing_warning:
            st.error(f"🚨 {timing_warning}")
        elif "ANALYSIS ONLY" in timing_warning:
            st.info(f"📊 {timing_warning}")
        else:
            st.warning(f"⚠️ {timing_warning}")

def display_header_info(current_spy: float, price_source: str, trading_window_ok: bool, 
                       window_message: str, sandbox_mode: bool):
    """Display header information"""
    current_time = datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S ET")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.info(f"🕐 Current Time: {current_time}")
    with col2:
        if trading_window_ok:
            st.success(f"✅ Trading Window Open")
        else:
            st.warning(f"⚠️ {window_message.split('(')[0]}")
    with col3:
        api_status = "Production" if not sandbox_mode else "Sandbox"
        st.info(f"📡 API: {api_status}")
        st.caption(f"Price: {price_source}")

def display_price_targets(current_spy: float, price_targets: Dict):
    """Display system-calculated price targets"""
    st.header("🎯 System-Calculated Price Targets")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Current SPY", 
            f"${current_spy:.2f}",
            delta=f"Live Price"
        )
    
    with col2:
        upside_move = price_targets['upside_target'] - current_spy
        st.metric(
            "Upside Target", 
            f"${price_targets['upside_target']:.2f}",
            delta=f"+${upside_move:.2f} ({price_targets['upside_probability']}% prob)"
        )
    
    with col3:
        downside_move = current_spy - price_targets['downside_target']
        st.metric(
            "Downside Target", 
            f"${price_targets['downside_target']:.2f}",
            delta=f"-${downside_move:.2f} ({price_targets['downside_probability']}% prob)"
        )
    
    # Show target reasoning
    with st.expander("📋 Target Calculation Reasoning", expanded=False):
        for reason in price_targets['reasoning']:
            st.write(f"• {reason}")

def display_market_analysis_details(analysis: Dict):
    """Display detailed market analysis breakdown"""
    st.header("📋 Market Analysis Breakdown")
    
    # Gap Analysis Detail
    with st.expander("📊 Gap Analysis - Statistical Edge Detection", expanded=False):
        gap = analysis['gap_analysis']
        
        if gap.get('error'):
            st.error(f"⚠️ {gap['error']}")
        else:
            st.info(f"📊 **Data Source:** {gap.get('data_source', 'Unknown')}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Gap %", f"{gap['gap_pct']:.2f}%")
                st.caption(f"Category: {gap['gap_size_category']}")
                
            with col2:
                st.metric("VWAP Distance", f"{gap['vwap_distance_pct']:.3f}%")
                st.caption(gap['vwap_status'])
                
            with col3:
                st.metric("Volume Surge Ratio", f"{gap['volume_surge_ratio']:.2f}x")
                st.caption("vs average")
                    
            with col4:
                st.metric("Total Gap Points", f"{gap['total_points']:.1f}")
                st.caption("Weighted score")
    
    # Market Internals Detail
    with st.expander("🏛️ Market Internals - Proxy Calculations", expanded=False):
        internals = analysis['internals']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("$TICK Proxy", f"{internals['tick']['value']:,.0f}")
            st.caption(f"Signal: {internals['tick']['signal']}")
                
        with col2:
            st.metric("$TRIN Proxy", f"{internals['trin']['value']:.3f}")
            st.caption(f"Signal: {internals['trin']['signal']}")
                
        with col3:
            st.metric("NYAD Proxy", f"{internals['nyad']['value']:,.0f}")
            st.caption(f"Signal: {internals['nyad']['signal']}")
            
        with col4:
            st.metric("Volume Flow", f"{internals['vold']['value']:.2f}")
            st.caption(f"Signal: {internals['vold']['signal']}")
    
    # Enhanced Trend Analysis
    with st.expander("🆕 Enhanced Trend Analysis", expanded=False):
        trend_analysis = analysis.get('trend_analysis', {})
        momentum_shift = analysis.get('momentum_shift', {})
        dynamic_vwap = analysis.get('dynamic_vwap', {})
    
        if trend_analysis:
            col1, col2, col3 = st.columns(3)
        
            with col1:
                st.metric("EMA(9)", f"${trend_analysis.get('ema9_current', 0):.2f}")
                st.metric("EMA(20)", f"${trend_analysis.get('ema20_current', 0):.2f}")
            
            with col2:
                st.metric("EMA Separation", f"{trend_analysis.get('ema_separation', 0):+.3f}%")
                st.metric("Trend Strength", f"{trend_analysis.get('trend_strength', 0):.3f}%")
            
            with col3:
                st.metric("Market Regime", dynamic_vwap.get('regime', 'Unknown'))
                shift_status = "✅ DETECTED" if momentum_shift.get('shift_detected', False) else "❌ None"
                st.metric("Momentum Shift", shift_status)
        
            if momentum_shift.get('shift_detected', False):
                st.success(f"""
                🚨 **MOMENTUM SHIFT DETECTED**
                • 5-min momentum: {momentum_shift.get('momentum_5min', 0):+.2f}%
                • 10-min momentum: {momentum_shift.get('momentum_10min', 0):+.2f}%
                • Volume acceleration: {momentum_shift.get('volume_acceleration', 1):.1f}x
                • Contributing {momentum_shift.get('shift_points', 0):+.1f} points to decision
                """)

def display_final_recommendation(analysis: Dict, trading_window_ok: bool, window_message: str):
    """Display final trading recommendation"""
    st.header("🎯 Final Trading Recommendation")
    
    if analysis['decision'] != 'NO TRADE' and trading_window_ok:
        st.success(f"""
        ✅ **EXECUTE TRADE: {analysis['decision']}**
        
        **Signal Breakdown:**
        • Gap Analysis: {analysis['gap_analysis'].get('total_points', 0):.1f} points
        • Market Internals: {analysis['internals'].get('total_points', 0):.1f} points  
        • Sector Leadership: {analysis['sectors_enhanced'].get('total_points', 0):.1f} points
        • Technical Analysis: {analysis['technicals_enhanced'].get('total_points', 0):.1f} points
        • Trend Analysis: {analysis.get('decision_breakdown', {}).get('trend_contribution', 0):.1f} points
        """)
    elif not trading_window_ok:
        st.info(f"⏰ **MARKET STATUS** - {window_message}")
        
        if "closed" in window_message.lower():
            st.markdown("### 📊 After-Hours Analysis Available")
            st.write("Current analysis is based on last available market data.")
            st.write("This can help you prepare for tomorrow's trading session.")
    else:
        st.error("❌ **NO TRADE** - Insufficient signals or unfavorable conditions")
