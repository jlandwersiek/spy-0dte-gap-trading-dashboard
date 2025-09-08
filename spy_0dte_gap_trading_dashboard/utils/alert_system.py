"""Complete alert system for signal changes and exit safety"""
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import requests
from typing import Dict

class AlertSystem:
    """Comprehensive alert system for trading signals and exit safety"""
    
    def __init__(self):
        self.previous_signal = st.session_state.get('previous_signal')
        
    def check_and_send_alerts(self, current_analysis: Dict):
        """Check for signal changes and send configured alerts"""
        current_signal = current_analysis['decision']
        
        # Only alert if signal actually changed
        if self.previous_signal and self.previous_signal != current_signal:
            # Skip "NO TRADE - OUTSIDE WINDOW" changes (those are just timing)
            if not current_signal.startswith("NO TRADE - OUTSIDE"):
                self._send_all_alerts(self.previous_signal, current_signal, current_analysis)
        
        # Store current signal for next comparison
        st.session_state['previous_signal'] = current_signal
    
    def check_exit_alerts(self):
        """Check for exit-related safety alerts"""
        import pytz
        
        # Always check time-based alerts during trading hours
        time_alerts = self._check_time_based_exit_alerts()
        for alert in time_alerts:
            self._send_safety_alert(alert)
        
        # Check trade-specific alerts if tracking a position
        if st.session_state.get('active_trade'):
            try:
                # Get current P&L from exit signals if available
                active_trade = st.session_state['active_trade']
                
                # Try to get current P&L from the displayed exit signals
                # This is a simple approach - we'll use session state if exit signals were calculated
                current_pnl = st.session_state.get('current_trade_pnl', 0)
                
                # Calculate time in trade
                entry_time = active_trade['entry_time']
                current_time = datetime.now(pytz.timezone('US/Eastern'))
                time_in_trade_minutes = (current_time - entry_time).total_seconds() / 60
                
                # Check all exit alert types
                alerts = []
                alerts.extend(self._check_stop_loss_alerts(current_pnl))
                alerts.extend(self._check_profit_taking_alerts(current_pnl, time_in_trade_minutes))
                
                for alert in alerts:
                    self._send_safety_alert(alert)
                    
            except Exception as e:
                pass  # Fail silently
    
    def _send_all_alerts(self, old_signal: str, new_signal: str, analysis: Dict):
        """Send all enabled alert types"""
        alert_settings = st.session_state.get('alert_settings', {})
        
        if not alert_settings.get('enabled', False):
            return
            
        # Visual flash alert
        if 'Visual Flash' in alert_settings.get('types', []):
            self._visual_flash_alert(old_signal, new_signal)
        
        # Browser notification
        if 'Browser Notification' in alert_settings.get('types', []):
            self._browser_notification(old_signal, new_signal, analysis)
        
        # Sound alert
        if 'Sound Alert' in alert_settings.get('types', []):
            self._sound_alert(new_signal)
        
        # Email-to-SMS (preferred)
        if 'Email to SMS' in alert_settings.get('types', []):
            phone = alert_settings.get('phone_number')
            carrier = alert_settings.get('carrier')
            if phone and carrier:
                self._send_email_to_sms(old_signal, new_signal, phone, carrier, analysis)
        
        # Email fallback
        elif 'Email' in alert_settings.get('types', []):
            email = alert_settings.get('email_address')
            if email:
                self._send_email_alert(old_signal, new_signal, email, analysis)
    
    def _visual_flash_alert(self, old_signal: str, new_signal: str):
        """Flash the screen for visual alert"""
        flash_color = '#00ff00' if 'LONG' in new_signal else '#ff0000' if 'SHORT' in new_signal else '#ffff00'
        
        st.components.v1.html(f"""
        <script>
        // Create flash overlay
        const flashDiv = document.createElement('div');
        flashDiv.style.position = 'fixed';
        flashDiv.style.top = '0';
        flashDiv.style.left = '0';
        flashDiv.style.width = '100%';
        flashDiv.style.height = '100%';
        flashDiv.style.backgroundColor = '{flash_color}';
        flashDiv.style.opacity = '0.8';
        flashDiv.style.zIndex = '9999';
        flashDiv.style.pointerEvents = 'none';
        
        document.body.appendChild(flashDiv);
        
        // Flash animation - 3 quick flashes
        let flashCount = 0;
        const flashInterval = setInterval(() => {{
            flashDiv.style.opacity = flashDiv.style.opacity === '0' ? '0.8' : '0';
            flashCount++;
            if (flashCount >= 6) {{
                document.body.removeChild(flashDiv);
                clearInterval(flashInterval);
            }}
        }}, 200);
        </script>
        """, height=0)
        
        # Also show streamlit alert
        if 'LONG' in new_signal:
            st.success(f"SIGNAL CHANGE: {old_signal} → {new_signal}")
        elif 'SHORT' in new_signal:
            st.error(f"SIGNAL CHANGE: {old_signal} → {new_signal}")
        else:
            st.warning(f"SIGNAL CHANGE: {old_signal} → {new_signal}")
    
    def _browser_notification(self, old_signal: str, new_signal: str, analysis: Dict):
        """Send browser notification"""
        bullish_points = analysis.get('bullish_points', 0)
        bearish_points = analysis.get('bearish_points', 0)
        
        st.components.v1.html(f"""
        <script>
        function sendNotification() {{
            if (Notification.permission === 'granted') {{
                const notification = new Notification('SPY Signal Change', {{
                    body: '{old_signal} → {new_signal}\\nBullish: {bullish_points:.1f} | Bearish: {bearish_points:.1f}',
                    icon: '📈',
                    tag: 'spy-signal',
                    requireInteraction: true
                }});
                
                // Auto-close after 15 seconds
                setTimeout(() => notification.close(), 15000);
                
            }} else if (Notification.permission !== 'denied') {{
                Notification.requestPermission().then(permission => {{
                    if (permission === 'granted') {{
                        sendNotification();
                    }}
                }});
            }}
        }}
        sendNotification();
        </script>
        """, height=0)
    
    def _sound_alert(self, signal: str):
        """Play sound alert based on signal type"""
        if 'LONG' in signal:
            # C Major chord (C-E-G) for bullish
            st.components.v1.html("""
            <script>
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // C Major chord frequencies
            const frequencies = [261.63, 329.63, 392.00]; // C, E, G
            frequencies.forEach((freq, index) => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = freq;
                oscillator.type = 'sine';
                
                // Start all notes together for proper chord
                const startTime = audioContext.currentTime + 0.1;
                gainNode.gain.setValueAtTime(0, startTime);
                gainNode.gain.linearRampToValueAtTime(0.15, startTime + 0.05);
                gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 1.0);
                
                oscillator.start(startTime);
                oscillator.stop(startTime + 1.0);
            });
            </script>
            """, height=0)
        
        elif 'SHORT' in signal:
            # C Minor chord (C-Eb-G) for bearish
            st.components.v1.html("""
            <script>
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // C Minor chord frequencies
            const frequencies = [261.63, 311.13, 392.00]; // C, Eb, G
            frequencies.forEach((freq, index) => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = freq;
                oscillator.type = 'sine';
                
                // Start all notes together for proper chord
                const startTime = audioContext.currentTime + 0.1;
                gainNode.gain.setValueAtTime(0, startTime);
                gainNode.gain.linearRampToValueAtTime(0.15, startTime + 0.05);
                gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 1.0);
                
                oscillator.start(startTime);
                oscillator.stop(startTime + 1.0);
            });
            </script>
            """, height=0)
        
        else:
            # Single C note for neutral signals
            st.components.v1.html("""
            <script>
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 261.63; // C note
            oscillator.type = 'sine';
            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.15, audioContext.currentTime + 0.1);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
            </script>
            """, height=0)
    
    def _send_email_to_sms(self, old_signal: str, new_signal: str, phone: str, carrier: str, analysis: Dict):
        """Send SMS via carrier email gateway (free)"""
        try:
            # Carrier email gateways
            gateways = {
                'Verizon': '@vtext.com',
                'AT&T': '@txt.att.net', 
                'T-Mobile': '@tmomail.net',
                'Sprint': '@messaging.sprintpcs.com',
                'Boost Mobile': '@sms.myboostmobile.com',
                'Cricket': '@sms.cricketwireless.net',
                'US Cellular': '@email.uscc.net',
                'Metro PCS': '@mymetropcs.com',
                'Virgin Mobile': '@vmobl.com',
                'Tracfone': '@mmst5.tracfone.com'
            }
            
            # Clean phone number
            clean_phone = phone.replace('+1', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            
            # Create SMS email address
            sms_email = f"{clean_phone}{gateways.get(carrier, '@vtext.com')}"
            
            # Short message for SMS (160 char limit)
            short_message = f"SPY: {old_signal} -> {new_signal} | Bull:{analysis.get('bullish_points', 0):.1f} Bear:{analysis.get('bearish_points', 0):.1f} | {datetime.now().strftime('%H:%M')}"
            
            # Send via email
            self._send_email_message(sms_email, "SPY Alert", short_message)
            
            st.success("SMS alert sent!")
            
        except Exception as e:
            st.error(f"SMS alert error: {str(e)}")
            # Try email fallback
            email = st.session_state.get('alert_settings', {}).get('email_address')
            if email:
                self._send_email_alert(old_signal, new_signal, email, analysis)
    
    def _send_email_alert(self, old_signal: str, new_signal: str, email: str, analysis: Dict):
        """Send email alert"""
        try:
            subject = f"SPY Signal Change: {new_signal}"
            
            body = f"""SPY 0DTE Signal Change Alert
            
Signal Changed: {old_signal} → {new_signal}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S ET')}

Analysis Breakdown:
- Bullish Points: {analysis.get('bullish_points', 0):.1f}
- Bearish Points: {analysis.get('bearish_points', 0):.1f}
- Confidence: {analysis.get('confidence', 'Unknown')}

Trading Window: {analysis.get('window_message', 'Check dashboard')}

Check your dashboard for complete details and exit signals.
"""
            
            self._send_email_message(email, subject, body)
            st.success("Email alert sent!")
            
        except Exception as e:
            st.error(f"Email alert error: {str(e)}")
    
    def _send_email_message(self, to_email: str, subject: str, body: str):
        """Send email message using Gmail SMTP"""
        sender_email = st.secrets.get("ALERT_EMAIL", "")
        sender_password = st.secrets.get("ALERT_EMAIL_PASSWORD", "")
        
        if not sender_email or not sender_password:
            st.warning("Email credentials not configured in Streamlit secrets")
            return
        
        message = MIMEText(body)
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = to_email
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())

    def _check_time_based_exit_alerts(self):
        """Check for time-based safety warnings"""
        import pytz
        alerts = []
        
        miami_time = datetime.now(pytz.timezone('US/Eastern'))
        
        # Only check during weekdays
        if miami_time.weekday() >= 5:
            return alerts
        
        market_close = miami_time.replace(hour=16, minute=0, second=0, microsecond=0)
        minutes_to_close = (market_close - miami_time).total_seconds() / 60
        
        # Use session state to prevent duplicate alerts
        last_time_alert = st.session_state.get('last_time_alert_minutes', 0)
        
        if 30 <= minutes_to_close <= 32 and last_time_alert != 30:
            st.session_state['last_time_alert_minutes'] = 30
            alerts.append({
                'type': 'TIME_WARNING',
                'urgency': 'HIGH',
                'message': 'THETA BURN ALERT: 30 minutes to close - Consider closing 0DTE positions',
                'sound': 'warning'
            })
        
        elif 60 <= minutes_to_close <= 62 and last_time_alert != 60:
            st.session_state['last_time_alert_minutes'] = 60
            alerts.append({
                'type': 'TIME_WARNING',
                'urgency': 'MEDIUM',
                'message': 'TIME CHECK: 1 hour to close - Review open positions',
                'sound': 'neutral'
            })
        
        elif 15 <= minutes_to_close <= 17 and last_time_alert != 15:
            st.session_state['last_time_alert_minutes'] = 15
            alerts.append({
                'type': 'TIME_WARNING',
                'urgency': 'CRITICAL',
                'message': 'FINAL WARNING: 15 minutes to close - Close all 0DTE positions now',
                'sound': 'urgent'
            })
        
        return alerts

    def _check_stop_loss_alerts(self, current_pnl_pct: float):
        """Check for stop loss tier warnings"""
        alerts = []
        
        # Use session state to prevent spam alerts
        last_stop_alert = st.session_state.get('last_stop_loss_alert', 0)
        
        if -25 <= current_pnl_pct <= -23 and last_stop_alert != -25:
            st.session_state['last_stop_loss_alert'] = -25
            alerts.append({
                'type': 'STOP_LOSS',
                'urgency': 'MEDIUM', 
                'message': f'RISK WARNING: Down {current_pnl_pct:.1f}% - Consider exit before -30%',
                'sound': 'warning'
            })
        
        elif -35 <= current_pnl_pct <= -33 and last_stop_alert != -35:
            st.session_state['last_stop_loss_alert'] = -35
            alerts.append({
                'type': 'STOP_LOSS',
                'urgency': 'HIGH',
                'message': f'STOP LOSS ZONE: Down {current_pnl_pct:.1f}% - Exit recommended',
                'sound': 'warning'
            })
        
        elif current_pnl_pct <= -50 and last_stop_alert != -50:
            st.session_state['last_stop_loss_alert'] = -50
            alerts.append({
                'type': 'STOP_LOSS',
                'urgency': 'CRITICAL',
                'message': f'MAJOR LOSS: Down {current_pnl_pct:.1f}% - CLOSE POSITION IMMEDIATELY',
                'sound': 'urgent'
            })
        
        return alerts

    def _check_profit_taking_alerts(self, current_pnl_pct: float, time_in_trade_minutes: float):
        """Check for profit-taking opportunities"""
        alerts = []
        
        # Use session state to prevent spam alerts
        last_profit_alert = st.session_state.get('last_profit_alert', 0)
        
        if 20 <= current_pnl_pct <= 22 and time_in_trade_minutes <= 30 and last_profit_alert != 20:
            st.session_state['last_profit_alert'] = 20
            alerts.append({
                'type': 'PROFIT_TAKING',
                'urgency': 'MEDIUM',
                'message': f'QUICK PROFIT: Up {current_pnl_pct:.1f}% in {time_in_trade_minutes:.0f} min - Consider taking gains',
                'sound': 'profit'
            })
        
        elif current_pnl_pct >= 50 and last_profit_alert != 50:
            st.session_state['last_profit_alert'] = 50
            alerts.append({
                'type': 'PROFIT_TAKING', 
                'urgency': 'HIGH',
                'message': f'MAJOR GAIN: Up {current_pnl_pct:.1f}% - Strong exit signal',
                'sound': 'profit'
            })
        
        return alerts

    def _send_safety_alert(self, alert: Dict):
        """Send safety-focused exit alert"""
        alert_settings = st.session_state.get('alert_settings', {})
        
        if not alert_settings.get('exit_alerts_enabled', False):
            return
        
        # Visual alert
        if alert['urgency'] == 'CRITICAL':
            st.error(f"🚨 {alert['message']}")
        elif alert['urgency'] == 'HIGH':
            st.warning(f"⚠️ {alert['message']}")
        else:
            st.info(f"ℹ️ {alert['message']}")
        
        # Sound alert if enabled
        if 'Sound Alert' in alert_settings.get('types', []):
            if alert.get('sound') == 'warning':
                self._play_warning_sound()
            elif alert.get('sound') == 'urgent':
                self._play_urgent_sound()
            elif alert.get('sound') == 'profit':
                self._play_profit_sound()

    def _play_warning_sound(self):
        """Play warning sound (diminished chord)"""
        st.components.v1.html("""
        <script>
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const frequencies = [261.63, 311.13, 369.99]; // C, Eb, F# (diminished)
        frequencies.forEach(freq => {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            oscillator.frequency.value = freq;
            oscillator.type = 'sine';
            const startTime = audioContext.currentTime + 0.1;
            gainNode.gain.setValueAtTime(0, startTime);
            gainNode.gain.linearRampToValueAtTime(0.1, startTime + 0.05);
            gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.8);
            oscillator.start(startTime);
            oscillator.stop(startTime + 0.8);
        });
        </script>
        """, height=0)

    def _play_urgent_sound(self):
        """Play urgent sound (rapid beeps)"""
        st.components.v1.html("""
        <script>
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        for(let i = 0; i < 3; i++) {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            oscillator.frequency.value = 440;
            oscillator.type = 'square';
            const startTime = audioContext.currentTime + (i * 0.3);
            gainNode.gain.setValueAtTime(0, startTime);
            gainNode.gain.linearRampToValueAtTime(0.2, startTime + 0.05);
            gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.2);
            oscillator.start(startTime);
            oscillator.stop(startTime + 0.2);
        }
        </script>
        """, height=0)

    def _play_profit_sound(self):
        """Play profit sound (ascending major scale)"""
        st.components.v1.html("""
        <script>
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const frequencies = [261.63, 293.66, 329.63]; // C, D, E (ascending)
        frequencies.forEach((freq, index) => {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            oscillator.frequency.value = freq;
            oscillator.type = 'sine';
            const startTime = audioContext.currentTime + (index * 0.15);
            gainNode.gain.setValueAtTime(0, startTime);
            gainNode.gain.linearRampToValueAtTime(0.1, startTime + 0.05);
            gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.3);
            oscillator.start(startTime);
            oscillator.stop(startTime + 0.3);
        });
        </script>
        """, height=0)

def setup_alert_ui():
    """Setup alert configuration UI in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.header("Alert System")
    
    enable_alerts = st.sidebar.checkbox("Enable Signal Change Alerts", value=False)
    
    alert_settings = {'enabled': enable_alerts}
    
    if enable_alerts:
        st.sidebar.markdown("**Visual/Audio Alerts:**")
        alert_types = []
        
        if st.sidebar.checkbox("Visual Flash", value=True):
            alert_types.append("Visual Flash")
        if st.sidebar.checkbox("Browser Notification", value=True):
            alert_types.append("Browser Notification")
        if st.sidebar.checkbox("Sound Alert", value=True):
            alert_types.append("Sound Alert")
        
        st.sidebar.markdown("**Message Alerts:**")
        
        message_type = st.sidebar.radio(
            "Choose message type:",
            ["None", "Free SMS (Email Gateway)", "Email Only"]
        )
        
        if message_type == "Free SMS (Email Gateway)":
            phone_number = st.sidebar.text_input(
                "Phone Number", 
                placeholder="1234567890",
                help="Enter 10-digit phone number (no country code needed for US)"
            )
            
            carrier = st.sidebar.selectbox(
                "Phone Carrier:", 
                [
                    "Verizon",
                    "AT&T", 
                    "T-Mobile",
                    "Sprint",
                    "Boost Mobile",
                    "Cricket",
                    "US Cellular",
                    "Metro PCS",
                    "Virgin Mobile",
                    "Tracfone"
                ]
            )
            
            # Email fallback
            email_fallback = st.sidebar.text_input(
                "Email Fallback (if SMS fails)",
                placeholder="your.email@gmail.com",
                help="Optional: Email to use if SMS fails"
            )
            
            alert_types.append("Email to SMS")
            alert_settings.update({
                'phone_number': phone_number, 
                'carrier': carrier,
                'email_address': email_fallback
            })
            
            if phone_number and len(phone_number.replace('-', '').replace(' ', '')) != 10:
                st.sidebar.warning("Phone number should be 10 digits")
        
        elif message_type == "Email Only":
            email_address = st.sidebar.text_input(
                "Email Address",
                placeholder="your.email@gmail.com"
            )
            alert_types.append("Email")
            alert_settings['email_address'] = email_address
        
        alert_settings['types'] = alert_types
        
        # Exit safety alerts
        st.sidebar.markdown("**Exit Safety Alerts:**")
        exit_alerts = st.sidebar.checkbox("Enable Exit Safety Alerts", value=True)
        alert_settings['exit_alerts_enabled'] = exit_alerts
        
        # Email setup info
        if message_type != "None":
            with st.sidebar.expander("Email Setup Info"):
                st.write("""
                **Required Streamlit Secrets:**
                ```
                ALERT_EMAIL = "your.alerts@gmail.com"
                ALERT_EMAIL_PASSWORD = "your_app_password"
                ```
                
                **Gmail Setup:**
                1. Enable 2-factor authentication
                2. Generate App Password
                3. Use App Password (not regular password)
                """)
        
        # Test alert button
        if st.sidebar.button("Test Alerts"):
            if alert_types:
                # Create fake analysis for testing
                test_analysis = {
                    'decision': 'STRONG LONG',
                    'bullish_points': 8.5,
                    'bearish_points': 2.1,
                    'confidence': 'HIGH',
                    'window_message': 'Test alert triggered'
                }
                
                alert_system = AlertSystem()
                st.session_state['previous_signal'] = 'NO TRADE'
                alert_system._send_all_alerts('NO TRADE', 'STRONG LONG', test_analysis)
                st.sidebar.success("Test alerts sent!")
            else:
                st.sidebar.warning("Select at least one alert type")
    
    # Store settings in session state
    st.session_state['alert_settings'] = alert_settings
    
    return alert_settings
