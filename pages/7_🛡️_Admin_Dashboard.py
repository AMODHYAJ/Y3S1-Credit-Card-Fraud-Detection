import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.helpers import update_transaction_status, create_fraud_alert, convert_to_serializable, send_real_time_alert, generate_fraud_report
from utils.analytics import FraudAnalytics

from utils.session_utils import initialize_session_state
initialize_session_state()

st.set_page_config(page_title="Bank Security Dashboard", layout="wide")
st.title("🛡️ Bank Security Intelligence Dashboard")

# Admin authentication check
if not st.session_state.get('admin_authenticated', False):
    st.error("🔒 Access Denied: Admin authentication required")
    st.page_link("pages/6_👨💼_Admin_Login.py", label="Go to Admin Login", icon="🛡️")
    st.stop()

def load_pending_approvals():
    try:
        with open('data/pending_approvals.json', 'r') as f:
            return json.load(f)
    except:
        return []

def load_users():
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def load_fraud_alerts():
    try:
        with open('data/fraud_alerts.json', 'r') as f:
            return json.load(f)
    except:
        return []

def load_transactions():
    try:
        with open('data/transactions.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def detect_potential_criminal(user_id):
    """Analyze user patterns to detect potential criminal activity"""
    try:
        with open('data/transactions.json', 'r') as f:
            all_transactions = json.load(f)
        with open('data/pending_approvals.json', 'r') as f:
            pending = json.load(f)
    except:
        return False, []
    
    user_transactions = all_transactions.get(user_id, [])
    user_pending = [p for p in pending if p['user_id'] == user_id and p['status'] == 'pending']
    
    red_flags = []
    
    # 1. New user with multiple high-risk transactions
    if len(user_transactions) == 0 and len(user_pending) > 2:
        red_flags.append("New user with multiple pending high-risk transactions")
    
    # 2. Rapid transaction attempts
    if len(user_pending) >= 3:
        recent_times = []
        for pending_tx in user_pending[-3:]:
            try:
                tx_time = datetime.fromisoformat(pending_tx['timestamp'].replace('Z', '+00:00'))
                recent_times.append(tx_time)
            except:
                continue
        
        if len(recent_times) >= 3:
            time_diffs = [(recent_times[i] - recent_times[i-1]).total_seconds() for i in range(1, len(recent_times))]
            if any(diff < 600 for diff in time_diffs):  # Multiple transactions within 10 minutes
                red_flags.append("Rapid transaction attempts (multiple within 10 minutes)")
    
    # 3. High cumulative risk score
    total_risk = sum(tx['fraud_probability'] for tx in user_pending)
    if total_risk > 2.0:  # Very high cumulative risk
        red_flags.append(f"Very high cumulative risk score: {total_risk:.2f}")
    
    # 4. Geographic anomalies across transactions
    locations = []
    for tx in user_pending:
        tx_data = tx['transaction_data']
        if tx_data.get('merch_lat') and tx_data.get('merch_lon'):
            locations.append((tx_data['merch_lat'], tx_data['merch_lon']))
    
    if len(locations) >= 2:
        # Check if transactions are from very different locations
        lat_range = max(lat for lat, lon in locations) - min(lat for lat, lon in locations)
        lon_range = max(lon for lat, lon in locations) - min(lon for lat, lon in locations)
        if lat_range > 5.0 or lon_range > 5.0:  # Large geographic spread
            red_flags.append("Transactions from geographically dispersed locations")
    
    # 5. Unusual transaction amounts
    pending_amounts = [tx['transaction_data']['amount'] for tx in user_pending]
    if pending_amounts:
        avg_amount = sum(pending_amounts) / len(pending_amounts)
        if any(amount > avg_amount * 10 for amount in pending_amounts):  # 10x average amount
            red_flags.append("Extremely high amount transactions")
    
    # 6. Multiple high-risk transactions
    high_risk_count = len([tx for tx in user_pending if tx['risk_level'] == 'HIGH_RISK'])
    if high_risk_count >= 2:
        red_flags.append(f"Multiple high-risk transactions: {high_risk_count}")
    
    is_potential_criminal = len(red_flags) >= 2
    return is_potential_criminal, red_flags

def get_user_profile(user_id):
    """Get comprehensive user profile for investigation"""
    users = load_users()
    transactions = load_transactions()
    pending_approvals = load_pending_approvals()
    
    user_data = users.get(user_id, {})
    user_txs = transactions.get(user_id, [])
    user_pending = [p for p in pending_approvals if p['user_id'] == user_id]
    
    profile = {
        'user_data': user_data,
        'total_transactions': len(user_txs),
        'pending_transactions': len(user_pending),
        'account_age': None,
        'high_risk_count': len([tx for tx in user_pending if tx.get('risk_level') == 'HIGH_RISK']),
        'total_amount_pending': sum(tx['transaction_data']['amount'] for tx in user_pending)
    }
    
    # Calculate account age
    if user_data.get('account_created'):
        try:
            created_date = datetime.fromisoformat(user_data['account_created'].replace('Z', '+00:00'))
            account_age = (datetime.now() - created_date).days
            profile['account_age'] = account_age
        except:
            pass
    
    return profile

def approve_transaction(transaction_id, user_id, amount):
    """Finalize transaction approval - balance already reserved"""
    try:
        # Transaction is already approved, just update status
        update_transaction_status(transaction_id, 'approved', 'Transaction approved by security team')
        st.success(f"✅ Transaction {transaction_id} approved!")
        return True
    except Exception as e:
        st.error(f"Error approving transaction: {e}")
        return False

def reject_transaction(transaction_id, user_id, amount):
    """Refund reserved credit when transaction is rejected"""
    try:
        # Read current users data
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        
        if user_id in users:
            user = users[user_id]
            
            # Refund the reserved credit
            current_available = user.get('total_available_credit', 0)
            user['total_available_credit'] = current_available + amount
            
            current_balance = user.get('total_current_balance', 0)
            user['total_current_balance'] = max(0, current_balance - amount)
            
            # Update primary card balance
            if 'credit_cards' in user and 'primary' in user['credit_cards']:
                card = user['credit_cards']['primary']
                card_available = card.get('available_balance', current_available)
                card['available_balance'] = card_available + amount
                card['current_balance'] = max(0, card.get('current_balance', 0) - amount)
            
            # Write back to file
            with open('data/users.json', 'w') as f:
                json.dump(users, f, indent=2, default=str)
        
        # Update transaction status
        update_transaction_status(transaction_id, 'rejected', 'Transaction rejected by security team - credit refunded')
        st.success(f"❌ Transaction {transaction_id} rejected and credit refunded!")
        return True
        
    except Exception as e:
        st.error(f"Error rejecting transaction: {e}")
        return False

def flag_transaction_as_fraud(transaction_id, user_id, amount, transaction_data, fraud_probability):
    """Flag transaction as fraud and refund credit"""
    try:
        # Refund the reserved credit (same as reject)
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        
        if user_id in users:
            user = users[user_id]
            current_available = user.get('total_available_credit', 0)
            user['total_available_credit'] = current_available + amount
            
            current_balance = user.get('total_current_balance', 0)
            user['total_current_balance'] = max(0, current_balance - amount)
            
            if 'credit_cards' in user and 'primary' in user['credit_cards']:
                card = user['credit_cards']['primary']
                card_available = card.get('available_balance', current_available)
                card['available_balance'] = card_available + amount
                card['current_balance'] = max(0, card.get('current_balance', 0) - amount)
            
            with open('data/users.json', 'w') as f:
                json.dump(users, f, indent=2, default=str)
        
        # Update transaction status and create fraud alert
        update_transaction_status(transaction_id, 'fraud', 'Flagged as fraudulent activity - credit refunded')
        create_fraud_alert(transaction_data, fraud_probability)
        
        st.error("🚨 Transaction flagged as fraud! Credit refunded and authorities notified.")
        return True
        
    except Exception as e:
        st.error(f"Error flagging transaction as fraud: {e}")
        return False

# Load data
pending_approvals = load_pending_approvals()
fraud_alerts = load_fraud_alerts()
users = load_users()
transactions = load_transactions()

# Initialize analytics
analytics = FraudAnalytics()
performance_metrics = analytics.calculate_performance_metrics()

# Welcome message
st.success(f"Welcome, {st.session_state.admin_details.get('name', 'Admin')}! 👨💼 • Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# =============================================================================
# REAL-TIME DASHBOARD METRICS
# =============================================================================

st.subheader("📊 Real-time Security Intelligence")

# Top level metrics
col1, col2, col3, col4, col5 = st.columns(5)

active_alerts = [a for a in fraud_alerts if a['status'] == 'new']
high_risk_pending = [p for p in pending_approvals if p['risk_level'] == 'HIGH_RISK' and p['status'] == 'pending']
suspicious_users = []

# Check for suspicious users
for user_id in users.keys():
    is_suspicious, _ = detect_potential_criminal(user_id)
    if is_suspicious:
        suspicious_users.append(user_id)

with col1:
    st.metric(
        "Pending Approvals", 
        len(pending_approvals),
        delta=f"{len(high_risk_pending)} high risk"
    )

with col2:
    st.metric(
        "Active Fraud Alerts", 
        len(active_alerts),
        delta="🔄 Real-time"
    )

with col3:
    st.metric(
        "Suspicious Users", 
        len(suspicious_users),
        delta="👮 Monitor"
    )

with col4:
    st.metric(
        "Blocked Fraud", 
        performance_metrics.get('resolved_alerts', 0),
        delta=f"${performance_metrics.get('total_fraud_amount', 0):,}"
    )

with col5:
    success_rate = performance_metrics.get('resolution_rate', 0)
    st.metric(
        "Success Rate", 
        f"{success_rate:.1f}%",
        delta="🎯 Accuracy" if success_rate > 80 else "⚠️ Needs Attention"
    )

# =============================================================================
# VISUALIZATION CHARTS
# =============================================================================

col1, col2 = st.columns(2)

with col1:
    # Risk Distribution Chart
    if pending_approvals:
        risk_data = []
        for approval in pending_approvals:
            if approval['status'] == 'pending':
                risk_data.append({
                    'risk_level': approval['risk_level'],
                    'amount': approval['transaction_data']['amount']
                })
        
        if risk_data:
            risk_df = pd.DataFrame(risk_data)
            risk_counts = risk_df['risk_level'].value_counts()
            
            fig_risk = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                title="📈 Risk Level Distribution",
                color=risk_counts.index,
                color_discrete_map={
                    'HIGH_RISK': '#FF6B6B',
                    'MEDIUM_RISK': '#FFD93D', 
                    'LOW_RISK': '#6BCF7F'
                }
            )
            st.plotly_chart(fig_risk, use_container_width=True)

with col2:
    # Fraud Trends Over Time
    daily_trends = analytics.get_daily_fraud_trends(days=7)
    if daily_trends:
        trend_df = pd.DataFrame(list(daily_trends.items()), columns=['Date', 'Fraud Alerts'])
        trend_df['Date'] = pd.to_datetime(trend_df['Date'])
        trend_df = trend_df.sort_values('Date')
        
        fig_trend = px.line(
            trend_df,
            x='Date',
            y='Fraud Alerts',
            title="📈 Fraud Alerts Trend (7 Days)",
            markers=True
        )
        fig_trend.update_traces(line=dict(color='#FF6B6B', width=3))
        st.plotly_chart(fig_trend, use_container_width=True)

# =============================================================================
# ENHANCED QUICK ACTIONS
# =============================================================================

st.subheader("🚀 Security Operations Center")

action_col1, action_col2, action_col3, action_col4 = st.columns(4)

with action_col1:
    if st.button("🔄 Refresh Intelligence", use_container_width=True):
        st.rerun()

with action_col2:
    if st.button("📊 Generate Report", use_container_width=True):
        report = generate_fraud_report('weekly')
        if 'error' not in report:
            st.success(f"""
            📋 Security Report Generated!
            
            **Key Metrics:**
            - Total Transactions: {report['total_transactions']:,}
            - Fraud Alerts: {report['fraud_alerts_generated']}
            - Resolution Rate: {report['resolution_rate']:.1f}%
            - Estimated Fraud Prevented: ${report['estimated_fraud_prevented']:,.2f}
            """)
        else:
            st.error("Failed to generate report")

with action_col3:
    if st.button("👮 Mass Alert", use_container_width=True):
        if suspicious_users:
            st.warning(f"🚨 Law enforcement notified for {len(suspicious_users)} suspicious users")
            # Log this action
            alert_log = {
                'action': 'mass_alert',
                'users_affected': len(suspicious_users),
                'timestamp': str(datetime.now()),
                'admin': st.session_state.admin_user
            }
            st.json(alert_log)
        else:
            st.info("No suspicious users to alert")

with action_col4:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.session_state.admin_user = None
        st.session_state.admin_details = {}
        st.rerun()

# =============================================================================
# REAL-TIME FRAUD ALERT SYSTEM
# =============================================================================

st.subheader("🚨 Real-time Fraud Alert System")

# High priority alerts at the top
high_priority_alerts = [a for a in active_alerts if a.get('priority') == 'HIGH']

if high_priority_alerts:
    st.error("🔴 CRITICAL ALERTS REQUIRING IMMEDIATE ATTENTION")
    
    for alert in high_priority_alerts:
        with st.expander(f"🚨 CRITICAL: {alert['alert_id']} | ${alert['amount']:,.2f} | {alert['priority']} PRIORITY", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Alert ID:** {alert['alert_id']}")
                st.write(f"**User ID:** {alert['user_id']}")
                st.write(f"**Amount:** ${alert['amount']:,.2f}")
                st.write(f"**Fraud Probability:** {alert['fraud_probability']:.2%}")
                
            with col2:
                st.write(f"**Merchant:** {alert['merchant']}")
                st.write(f"**Timestamp:** {alert['timestamp']}")
                st.write(f"**Urgency:** 🔴 IMMEDIATE ACTION REQUIRED")
            
            # Immediate action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Resolve Alert", key=f"resolve_critical_{alert['alert_id']}"):
                    alert['status'] = 'resolved'
                    alert['resolved_by'] = st.session_state.admin_user
                    alert['resolved_at'] = str(datetime.now())
                    with open('data/fraud_alerts.json', 'w') as f:
                        json.dump(fraud_alerts, f, indent=2)
                    st.success("Critical alert resolved!")
                    st.rerun()
            with col2:
                if st.button("🚓 Notify Police", key=f"police_critical_{alert['alert_id']}"):
                    st.error("🚓 Police department notified - case escalated!")
            with col3:
                if st.button("📞 Contact User", key=f"contact_critical_{alert['alert_id']}"):
                    st.info("User contact protocol initiated")

# =============================================================================
# PENDING TRANSACTIONS FOR APPROVAL
# =============================================================================

st.subheader("⏳ Pending Transaction Approvals")

if not pending_approvals:
    st.info("🎉 No pending transactions for approval")
else:
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        risk_filter = st.selectbox("Filter by Risk Level", ["All", "HIGH_RISK", "MEDIUM_RISK", "LOW_RISK"])
    with col2:
        sort_by = st.selectbox("Sort Transactions By", ["Risk Level", "Amount", "Date"])
    
    filtered_approvals = [p for p in pending_approvals if p['status'] == 'pending']
    
    if risk_filter != "All":
        filtered_approvals = [p for p in filtered_approvals if p['risk_level'] == risk_filter]
    
    # Sort approvals
    if sort_by == "Risk Level":
        risk_order = {"HIGH_RISK": 3, "MEDIUM_RISK": 2, "LOW_RISK": 1}
        filtered_approvals.sort(key=lambda x: risk_order.get(x['risk_level'], 0), reverse=True)
    elif sort_by == "Amount":
        filtered_approvals.sort(key=lambda x: x['transaction_data']['amount'], reverse=True)
    elif sort_by == "Date":
        filtered_approvals.sort(key=lambda x: x['timestamp'], reverse=True)
    
    for approval in filtered_approvals[:10]:  # Show first 10 to avoid overload
        # Criminal detection for each transaction
        is_suspicious, red_flags = detect_potential_criminal(approval['user_id'])
        
        risk_color = {
            'HIGH_RISK': 'red',
            'MEDIUM_RISK': 'orange', 
            'LOW_RISK': 'green'
        }.get(approval['risk_level'], 'gray')
        
        with st.expander(f":{risk_color}[**TX: {approval['transaction_id']}**] | ${approval['transaction_data']['amount']:,.2f} | {approval['risk_level'].replace('_', ' ')} {'🚨 SUSPICIOUS' if is_suspicious else ''}"):
            
            if is_suspicious:
                st.error("🚨 **POTENTIAL CRIMINAL ACTIVITY DETECTED**")
                for flag in red_flags[:3]:
                    st.write(f"• {flag}")
                st.warning("**Recommendation:** Immediate law enforcement notification recommended")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**User:** {approval['user_id']}")
                st.write(f"**Amount:** ${approval['transaction_data']['amount']:,.2f}")
                st.write(f"**Merchant:** {approval['transaction_data']['merchant_name']}")
                st.write(f"**Category:** {approval['transaction_data']['category']}")
                st.write(f"**Fraud Probability:** {approval['fraud_probability']:.2%}")
                
            with col2:
                st.write(f"**Submitted:** {approval['timestamp']}")
                st.write(f"**Risk Level:** {approval['risk_level']}")
                st.write(f"**Recipient:** {approval['transaction_data']['recipient_name']}")
                st.write(f"**Description:** {approval['transaction_data']['description']}")
            
            # Location information
            tx_data = approval['transaction_data']
            if tx_data.get('user_lat') and tx_data.get('user_lon'):
                st.write("**📍 Location Analysis:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"User Location: {tx_data['user_lat']:.4f}, {tx_data['user_lon']:.4f}")
                with col2:
                    st.write(f"Merchant Location: {tx_data['merch_lat']:.4f}, {tx_data['merch_lon']:.4f}")
                
                # Calculate distance
                distance = ((tx_data['merch_lat'] - tx_data['user_lat'])**2 + (tx_data['merch_lon'] - tx_data['user_lon'])**2)**0.5
                if distance > 1.0:
                    st.warning(f"⚠️ Unusual distance between locations: {distance:.2f} units")
            
            # Admin actions
            st.subheader("Admin Decision")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button(f"✅ Approve", key=f"approve_{approval['transaction_id']}"):
                    if approve_transaction(approval['transaction_id'], approval['user_id'], approval['transaction_data']['amount']):
                        st.rerun()
            
            with col2:
                if st.button(f"❌ Reject", key=f"reject_{approval['transaction_id']}"):
                    if reject_transaction(approval['transaction_id'], approval['user_id'], approval['transaction_data']['amount']):
                        st.rerun()
            
            with col3:
                if st.button(f"🚨 Flag as Fraud", key=f"flag_{approval['transaction_id']}"):
                    if flag_transaction_as_fraud(approval['transaction_id'], approval['user_id'], approval['transaction_data']['amount'], approval['transaction_data'], approval['fraud_probability']):
                        st.rerun()
            
            with col4:
                if is_suspicious and st.button(f"👮 Notify Police", key=f"police_{approval['transaction_id']}"):
                    st.error("🚓 **Law enforcement notified of potential criminal activity**")
                    # Create comprehensive criminal alert
                    criminal_alert = {
                        'alert_id': f"CRIMINAL_{int(datetime.now().timestamp())}",
                        'user_id': approval['user_id'],
                        'transaction_id': approval['transaction_id'],
                        'red_flags': red_flags,
                        'fraud_probability': approval['fraud_probability'],
                        'amount': approval['transaction_data']['amount'],
                        'timestamp': str(datetime.now()),
                        'priority': 'URGENT'
                    }
                    st.json(criminal_alert)

# =============================================================================
# SYSTEM PERFORMANCE ANALYTICS
# =============================================================================

st.subheader("📈 System Performance Analytics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Users", len(users))
    st.metric("Total Transactions", performance_metrics.get('total_alerts', 0))

with col2:
    st.metric("Resolution Rate", f"{performance_metrics.get('resolution_rate', 0):.1f}%")
    st.metric("High Risk Alerts", performance_metrics.get('high_risk_alerts', 0))

with col3:
    st.metric("Avg Fraud Amount", f"${performance_metrics.get('avg_fraud_amount', 0):,.2f}")
    st.metric("Total Fraud Amount", f"${performance_metrics.get('total_fraud_amount', 0):,.2f}")

# Footer
st.divider()
st.caption(f"SecureBank Fraud Detection System • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Logged in as: {st.session_state.admin_user}")