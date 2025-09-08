"""Points breakdown display with trend analysis"""
import streamlit as st
from typing import Dict

def display_points_breakdown_ui(analysis: Dict):
    """Display transparent points breakdown with trend analysis"""
    st.markdown("---")
    st.header("🔍 Enhanced Points System Breakdown")
    
    # Overall decision breakdown
    decision_breakdown = analysis.get('decision_breakdown', {})
    
    with st.expander("📊 Decision Logic Breakdown", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🟢 Bullish Points")
            st.metric("Gap Analysis", f"{max(0, decision_breakdown.get('gap_contribution', 0)):+.1f}")
            st.metric("Market Internals", f"{max(0, decision_breakdown.get('internals_contribution', 0)):+.1f}")
            st.metric("Sector Leadership", f"{max(0, decision_breakdown.get('sectors_contribution', 0)):+.1f}")
            st.metric("Technical Analysis", f"{max(0, decision_breakdown.get('technicals_contribution', 0)):+.1f}")
            st.metric("Volatility Factor", f"{max(0, decision_breakdown.get('volatility_contribution', 0)):+.1f}")
            st.metric("🆕 Trend Analysis", f"{max(0, decision_breakdown.get('trend_contribution', 0)):+.1f}")  # NEW
            st.metric("**TOTAL BULLISH**", f"**{decision_breakdown.get('bullish_total', 0):.1f}**")
        
        with col2:
            st.markdown("### 🔴 Bearish Points")
            st.metric("Gap Analysis", f"{max(0, -decision_breakdown.get('gap_contribution', 0)):+.1f}")
            st.metric("Market Internals", f"{max(0, -decision_breakdown.get('internals_contribution', 0)):+.1f}")
            st.metric("Sector Leadership", f"{max(0, -decision_breakdown.get('sectors_contribution', 0)):+.1f}")
            st.metric("Technical Analysis", f"{max(0, -decision_breakdown.get('technicals_contribution', 0)):+.1f}")
            st.metric("Volatility Factor", f"0.0")
            st.metric("🆕 Trend Analysis", f"{max(0, -decision_breakdown.get('trend_contribution', 0)):+.1f}")  # NEW
            st.metric("**TOTAL BEARISH**", f"**{decision_breakdown.get('bearish_total', 0):.1f}**")
        
        st.info(f"**Decision Logic:** {decision_breakdown.get('decision_logic', 'Logic not available')}")
    
    # NEW: Trend Analysis Details
    trend_analysis = analysis.get('trend_analysis', {})
    momentum_shift = analysis.get('momentum_shift', {})
    dynamic_vwap = analysis.get('dynamic_vwap', {})
    
    if trend_analysis or momentum_shift or dynamic_vwap:
        with st.expander("🆕 Trend Analysis Details", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**EMA Trend Analysis:**")
                st.write(f"• EMA Separation: {trend_analysis.get('ema_separation', 0):+.3f}%")
                st.write(f"• Trend Strength: {trend_analysis.get('trend_strength', 0):.3f}%")
                st.write(f"• Trend Acceleration: {trend_analysis.get('trend_acceleration', 0):+.3f}%")
                
                st.markdown("**Dynamic VWAP:**")
                st.write(f"• Market Regime: {dynamic_vwap.get('regime', 'Unknown')}")
                st.write(f"• Adjusted Threshold: {dynamic_vwap.get('adjusted_threshold', 0):.3f}%")
                st.write(f"• VWAP Points: {dynamic_vwap.get('points', 0):+.1f}")
            
            with col2:
                st.markdown("**Momentum Shift Detection:**")
                st.write(f"• Shift Detected: {'✅ YES' if momentum_shift.get('shift_detected', False) else '❌ NO'}")
                st.write(f"• 5-min Momentum: {momentum_shift.get('momentum_5min', 0):+.3f}%")
                st.write(f"• 10-min Momentum: {momentum_shift.get('momentum_10min', 0):+.3f}%")
                st.write(f"• Volume Acceleration: {momentum_shift.get('volume_acceleration', 1):.1f}x")
                st.write(f"• Shift Points: {momentum_shift.get('shift_points', 0):+.1f}")
                
                # Show momentum divergence calculation
                if momentum_shift.get('momentum_divergence', 0) > 0:
                    st.markdown("**Momentum Divergence:**")
                    st.write(f"• Divergence: {momentum_shift.get('momentum_divergence', 0):.3f}%")
                    if momentum_shift.get('momentum_divergence', 0) > 0.3:
                        st.success("🚨 Strong divergence detected!")
                    elif momentum_shift.get('momentum_divergence', 0) > 0.2:
                        st.warning("⚠️ Moderate divergence detected")
    
    # Detailed component breakdowns
    col1, col2 = st.columns(2)
    
    with col1:
        # Gap Analysis Details
        gap_breakdown = analysis.get('gap_analysis', {}).get('points_breakdown', {})
        if gap_breakdown:
            with st.expander("📊 Gap Analysis Points Detail"):
                for component, data in gap_breakdown.items():
                    if isinstance(data, dict) and 'points' in data:
                        st.write(f"**{component.replace('_', ' ').title()}:** {data['points']:+.1f} pts")
                        if 'reason' in data:
                            st.caption(data['reason'])
                
                # Show gap category explanation
                gap_pct = analysis.get('gap_analysis', {}).get('gap_pct', 0)
                gap_category = analysis.get('gap_analysis', {}).get('gap_size_category', 'UNKNOWN')
                if gap_pct != 0:
                    st.markdown("**Gap Analysis:**")
                    st.write(f"• Gap: {gap_pct:+.2f}% ({gap_category})")
                    st.write(f"• VWAP Distance: {analysis.get('gap_analysis', {}).get('vwap_distance_pct', 0):+.3f}%")
                    st.write(f"• Volume Surge: {analysis.get('gap_analysis', {}).get('volume_surge_ratio', 1):.1f}x")
        
        # Internals Details
        internals_breakdown = analysis.get('internals', {}).get('points_breakdown', {})
        if internals_breakdown:
            with st.expander("🏛️ Market Internals Points Detail"):
                for component, data in internals_breakdown.items():
                    if isinstance(data, dict) and 'points' in data:
                        st.write(f"**{component.upper()}:** {data['points']:+.1f} pts")
                        if 'reason' in data:
                            st.caption(data['reason'])
                
                # Show internals summary
                total_internals_points = internals_breakdown.get('total_points', 0)
                if total_internals_points != 0:
                    st.markdown("**Internals Summary:**")
                    if total_internals_points > 0:
                        st.success(f"✅ Bullish internals (+{total_internals_points:.1f} pts)")
                    elif total_internals_points < 0:
                        st.error(f"❌ Bearish internals ({total_internals_points:.1f} pts)")
                    else:
                        st.info("⚪ Neutral internals (0.0 pts)")
    
    with col2:
        # Sectors Details
        sectors_breakdown = analysis.get('sectors_enhanced', {}).get('points_breakdown', {})
        if sectors_breakdown:
            with st.expander("🏢 Sector Analysis Points Detail"):
                st.write(f"**Total Weighted Points:** {sectors_breakdown.get('total_weighted_points', 0):+.2f}")
                st.caption(sectors_breakdown.get('leadership_calculation', ''))
                st.caption(sectors_breakdown.get('rotation_logic', ''))
                
                # Show individual sector scores
                individual_scores = sectors_breakdown.get('individual_scores', {})
                if individual_scores:
                    st.markdown("**Top Performing Sectors:**")
                    # Sort by weighted score
                    sorted_sectors = sorted(individual_scores.items(), 
                                          key=lambda x: x[1].get('weighted_score', 0), reverse=True)
                    
                    for i, (symbol, data) in enumerate(sorted_sectors[:3]):  # Top 3
                        score = data.get('weighted_score', 0)
                        if score > 0:
                            st.write(f"• {symbol}: +{score:.3f} pts (Leading)")
                        elif score < 0:
                            st.write(f"• {symbol}: {score:.3f} pts (Lagging)")
        
        # Technicals Details
        technicals_breakdown = analysis.get('technicals_enhanced', {}).get('points_breakdown', {})
        if technicals_breakdown:
            with st.expander("📈 Technical Analysis Points Detail"):
                for component, data in technicals_breakdown.items():
                    if isinstance(data, dict) and 'points' in data:
                        st.write(f"**{component.replace('_', ' ').title()}:** {data['points']:+.1f} pts")
                        if 'reason' in data:
                            st.caption(data['reason'])
                
                # Show technical summary
                total_tech_points = technicals_breakdown.get('total_points', 0)
                vwap_analysis = analysis.get('technicals_enhanced', {}).get('vwap_analysis', {})
                if vwap_analysis:
                    st.markdown("**Technical Summary:**")
                    st.write(f"• Current: ${vwap_analysis.get('current_price', 0):.2f}")
                    st.write(f"• VWAP: ${vwap_analysis.get('vwap', 0):.2f}")
                    st.write(f"• Signal: {vwap_analysis.get('signal_strength', 'UNKNOWN')}")
                    
                    if total_tech_points > 0:
                        st.success(f"✅ Bullish technicals (+{total_tech_points:.1f} pts)")
                    elif total_tech_points < 0:
                        st.error(f"❌ Bearish technicals ({total_tech_points:.1f} pts)")
                    else:
                        st.info("⚪ Neutral technicals (0.0 pts)")

def display_trend_momentum_summary(analysis: Dict):
    """Display a compact trend momentum summary"""
    trend_analysis = analysis.get('trend_analysis', {})
    momentum_shift = analysis.get('momentum_shift', {})
    dynamic_vwap = analysis.get('dynamic_vwap', {})
    
    if not any([trend_analysis, momentum_shift, dynamic_vwap]):
        return
    
    with st.container():
        st.markdown("### 📈 Trend Momentum Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ema_sep = trend_analysis.get('ema_separation', 0)
            if abs(ema_sep) > 0.2:
                trend_status = "🔥 STRONG" if ema_sep > 0 else "❄️ STRONG"
                color = "green" if ema_sep > 0 else "red"
            elif abs(ema_sep) > 0.1:
                trend_status = "📈 MODERATE" if ema_sep > 0 else "📉 MODERATE"
                color = "orange" if ema_sep > 0 else "orange"
            else:
                trend_status = "➡️ RANGING"
                color = "gray"
            
            st.markdown(f"**EMA Trend**")
            st.markdown(f"<span style='color: {color}'>{trend_status}</span>", unsafe_allow_html=True)
            st.caption(f"{ema_sep:+.3f}% separation")
        
        with col2:
            regime = dynamic_vwap.get('regime', 'UNKNOWN')
            threshold = dynamic_vwap.get('adjusted_threshold', 0.15)
            
            if regime == "STRONG TREND":
                regime_emoji = "🚀"
                regime_color = "blue"
            elif regime == "MODERATE TREND":
                regime_emoji = "📊"
                regime_color = "orange"
            else:
                regime_emoji = "🔄"
                regime_color = "gray"
            
            st.markdown(f"**Market Regime**")
            st.markdown(f"<span style='color: {regime_color}'>{regime_emoji} {regime}</span>", unsafe_allow_html=True)
            st.caption(f"Threshold: {threshold:.3f}%")
        
        with col3:
            shift_detected = momentum_shift.get('shift_detected', False)
            shift_points = momentum_shift.get('shift_points', 0)
            
            if shift_detected:
                if shift_points > 0:
                    shift_status = "⬆️ BULLISH SHIFT"
                    shift_color = "green"
                else:
                    shift_status = "⬇️ BEARISH SHIFT"
                    shift_color = "red"
            else:
                shift_status = "⚪ NO SHIFT"
                shift_color = "gray"
            
            st.markdown(f"**Momentum Shift**")
            st.markdown(f"<span style='color: {shift_color}'>{shift_status}</span>", unsafe_allow_html=True)
            st.caption(f"{shift_points:+.1f} points")
        
        with col4:
            trend_contrib = analysis.get('decision_breakdown', {}).get('trend_contribution', 0)
            
            if trend_contrib > 1:
                contrib_status = "🟢 STRONG BULL"
                contrib_color = "green"
            elif trend_contrib > 0:
                contrib_status = "🟡 BULL"
                contrib_color = "orange"
            elif trend_contrib < -1:
                contrib_status = "🔴 STRONG BEAR"
                contrib_color = "red"
            elif trend_contrib < 0:
                contrib_status = "🟠 BEAR"
                contrib_color = "orange"
            else:
                contrib_status = "⚪ NEUTRAL"
                contrib_color = "gray"
            
            st.markdown(f"**Trend Impact**")
            st.markdown(f"<span style='color: {contrib_color}'>{contrib_status}</span>", unsafe_allow_html=True)
            st.caption(f"{trend_contrib:+.1f} net points")

def display_signal_strength_meter(analysis: Dict):
    """Display a visual signal strength meter"""
    bullish_points = analysis.get('bullish_points', 0)
    bearish_points = analysis.get('bearish_points', 0)
    decision = analysis.get('decision', 'NO TRADE')
    
    # Calculate signal strength (0-100)
    max_points = max(bullish_points, bearish_points)
    if max_points == 0:
        strength = 0
        direction = "NEUTRAL"
    elif bullish_points > bearish_points:
        strength = min(100, (bullish_points / 10) * 100)  # Scale to 100
        direction = "BULLISH"
    else:
        strength = min(100, (bearish_points / 10) * 100)
        direction = "BEARISH"
    
    # Color based on strength
    if strength >= 80:
        color = "#d4edda" if direction == "BULLISH" else "#f8d7da"
        strength_label = "VERY STRONG"
    elif strength >= 60:
        color = "#fff3cd" if direction == "BULLISH" else "#ffeaa7"
        strength_label = "STRONG"
    elif strength >= 40:
        color = "#e2e3e5"
        strength_label = "MODERATE"
    elif strength >= 20:
        color = "#f8f9fa"
        strength_label = "WEAK"
    else:
        color = "#f8f9fa"
        strength_label = "VERY WEAK"
    
    with st.container():
        st.markdown("### 🎯 Signal Strength Meter")
        
        # Progress bar
        st.progress(strength / 100, text=f"{direction} - {strength_label} ({strength:.0f}%)")
        
        # Additional context
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Signal Direction", direction)
        with col2:
            st.metric("Signal Strength", f"{strength:.0f}%")
        with col3:
            st.metric("Confidence", analysis.get('confidence', 'UNKNOWN'))
