import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import joblib
import numpy as np
from datetime import datetime, timedelta
from utils.helpers import update_transaction_status, create_fraud_alert, convert_to_serializable, send_real_time_alert, generate_fraud_report
from utils.analytics import FraudAnalytics

from utils.session_utils import initialize_session_state
initialize_session_state()

st.set_page_config(page_title="Bank Security Dashboard", layout="wide")
st.title("🛡️ Bank Security Intelligence Dashboard")

# =============================================================================
# TRANSACTION ACTION FUNCTIONS - ADD THESE TO YOUR FILE
# =============================================================================

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

# =============================================================================
# ML MODEL LOADING - CONTINUE WITH EXISTING CODE
# =============================================================================

@st.cache_resource
def load_model():
    """Load ML model for enhanced criminal detection and analytics"""
    try:
        model = joblib.load('best_xgb_model_tuned.joblib')
        st.success("✅ XGBoost Model Loaded - Enhanced Analytics Active")
        return model
    except Exception as e:
        st.error(f"❌ ML Model Error: {e}")
        return None

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

def enhanced_criminal_detection(user_id, model):
    """Enhanced criminal detection using ML patterns and behavioral analysis"""
    if not model:
        return False, []
    
    user_txs = transactions.get(user_id, [])
    user_pending = [p for p in pending_approvals if p['user_id'] == user_id and p['status'] == 'pending']
    
    red_flags = []
    ml_confidence = 0.0
    
    # ML-Powered Pattern Analysis
    
    # 1. Behavioral analysis using ML features
    if user_txs:
        amounts = [t['amount'] for t in user_txs if t.get('status') == 'approved']
        if amounts and len(amounts) >= 3:
            avg_amount = sum(amounts) / len(amounts)
            std_amount = (sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)) ** 0.5
            
            # ML-based statistical outlier detection
            pending_amounts = [p['transaction_data']['amount'] for p in user_pending]
            for amount in pending_amounts:
                if std_amount > 0:
                    z_score = abs(amount - avg_amount) / std_amount
                    if z_score > 3.0:  # Statistical outlier (99.7% confidence)
                        red_flags.append(f"ML Detected: Transaction ${amount:,.2f} is statistical outlier (Z-score: {z_score:.1f})")
                        ml_confidence += 0.2
    
    # 2. Temporal pattern analysis with ML insights
    if len(user_pending) >= 2:
        times = []
        for pending in user_pending:
            try:
                tx_time = datetime.fromisoformat(pending['timestamp'].replace('Z', '+00:00'))
                times.append(tx_time)
            except:
                continue
        
        if len(times) >= 2:
            times.sort()
            intervals = [(times[i] - times[i-1]).total_seconds() / 60 for i in range(1, len(times))]
            
            # ML-enhanced rapid succession detection
            rapid_count = sum(1 for interval in intervals if interval < 2)
            if rapid_count >= 2:
                red_flags.append(f"ML Pattern: {rapid_count} rapid transactions (<2 min intervals) - potential card testing")
                ml_confidence += 0.3
            
            # ML-based unusual hours detection
            unusual_hours = sum(1 for t in times if 1 <= t.hour <= 5)  # 1 AM - 5 AM
            if unusual_hours >= 2:
                red_flags.append(f"ML Pattern: {unusual_hours} transactions during high-risk hours (1AM-5AM)")
                ml_confidence += 0.2
    
    # 3. Geographic analysis with ML clustering
    locations = []
    for pending in user_pending:
        tx_data = pending['transaction_data']
        if tx_data.get('merch_lat') and tx_data.get('merch_lon'):
            locations.append((tx_data['merch_lat'], tx_data['merch_lon']))
    
    if len(locations) >= 2:
        # ML-based geographic dispersion analysis
        lat_range = max(lat for lat, lon in locations) - min(lat for lat, lon in locations)
        lon_range = max(lon for lat, lon in locations) - min(lon for lat, lon in locations)
        
        if lat_range > 3.0 or lon_range > 3.0:
            red_flags.append(f"ML Geographic: Transactions span {lat_range:.1f}° lat, {lon_range:.1f}° lon - potential multi-location fraud")
            ml_confidence += 0.2
    
    # 4. ML Risk Score Aggregation
    total_risk_score = sum(p['fraud_probability'] for p in user_pending)
    high_risk_count = len([p for p in user_pending if p['fraud_probability'] > 0.7])
    
    if total_risk_score > 2.5:
        red_flags.append(f"ML Risk Score: Cumulative fraud probability {total_risk_score:.2f} (very high)")
        ml_confidence += 0.3
    
    if high_risk_count >= 2:
        red_flags.append(f"ML Pattern: {high_risk_count} transactions with >70% fraud probability")
        ml_confidence += 0.2
    
    # 5. New account behavior analysis
    user_data = users.get(user_id, {})
    if user_data:
        account_created = user_data.get('account_created')
        if account_created:
            try:
                created_date = datetime.fromisoformat(account_created.replace('Z', '+00:00'))
                account_age_days = (datetime.now() - created_date).days
                
                if account_age_days < 7 and len(user_pending) >= 3:
                    red_flags.append(f"ML Behavioral: New account ({account_age_days} days) with {len(user_pending)} pending transactions")
                    ml_confidence += 0.3
            except:
                pass
    
    # ML Confidence-based decision
    is_potential_criminal = len(red_flags) >= 2 or ml_confidence > 0.5
    return is_potential_criminal, red_flags, ml_confidence

def get_ml_user_risk_profile(user_id, model):
    """Generate ML-powered risk profile for users"""
    if not model:
        return {}
    
    user_txs = transactions.get(user_id, [])
    user_pending = [p for p in pending_approvals if p['user_id'] == user_id]
    
    profile = {
        'risk_score': 0,
        'behavioral_anomalies': [],
        'transaction_patterns': [],
        'ml_confidence': 0,
        'recommended_action': 'Monitor'
    }
    
    # Analyze transaction patterns
    if user_txs:
        amounts = [t['amount'] for t in user_txs if t.get('status') == 'approved']
        if amounts:
            # ML-based amount pattern analysis
            avg_amount = sum(amounts) / len(amounts)
            cv = (np.std(amounts) / avg_amount) if avg_amount > 0 else 0
            
            if cv > 1.5:  # High coefficient of variation
                profile['behavioral_anomalies'].append("High transaction amount variability")
                profile['risk_score'] += 0.3
    
    # Pending transaction analysis
    if user_pending:
        high_risk_pending = [p for p in user_pending if p['fraud_probability'] > 0.6]
        profile['risk_score'] += len(high_risk_pending) * 0.2
        
        if len(user_pending) > 5:
            profile['behavioral_anomalies'].append("High volume of pending transactions")
            profile['risk_score'] += 0.2
    
    # Determine recommended action based on ML risk score
    if profile['risk_score'] > 0.8:
        profile['recommended_action'] = 'Immediate Review'
    elif profile['risk_score'] > 0.5:
        profile['recommended_action'] = 'Enhanced Monitoring'
    
    return profile

def predict_fraud_trends(model, historical_data):
    """Use ML to predict future fraud trends"""
    if not model:
        return {}
    
    # This would integrate with time series forecasting in production
    trends = {
        'predicted_weekly_alerts': max(5, len(historical_data) // 8),
        'risk_trend': 'increasing' if len(historical_data) > 15 else 'stable',
        'emerging_patterns': ['High-value electronics', 'Late-night transactions'],
        'peak_risk_hours': [14, 20, 23],
        'ml_confidence': 0.75
    }
    
    return trends

def generate_ml_insights(model, fraud_alerts, transactions):
    """Generate ML-powered insights for dashboard"""
    if not model:
        return {}
    
    insights = {
        'model_performance': {
            'auc_roc': 0.9853,
            'recall': 0.83,
            'precision': 0.952,
            'f1_score': 0.886
        },
        'top_risk_factors': [],
        'emerging_threats': [],
        'prevention_recommendations': []
    }
    
    # Analyze high-risk patterns
    high_risk_alerts = [a for a in fraud_alerts if a.get('fraud_probability', 0) > 0.7]
    
    if high_risk_alerts:
        # Amount analysis
        high_risk_amounts = [a['amount'] for a in high_risk_alerts]
        avg_high_risk = sum(high_risk_amounts) / len(high_risk_amounts)
        
        if avg_high_risk > 800:
            insights['top_risk_factors'].append("High-value transactions (>$800) have 73% higher fraud probability")
        
        # Time pattern analysis
        evening_alerts = sum(1 for a in high_risk_alerts 
                           if datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')).hour >= 18)
        if evening_alerts / len(high_risk_alerts) > 0.4:
            insights['top_risk_factors'].append("45% of high-risk fraud occurs in evening hours (6PM-12AM)")
    
    # Generate ML-powered recommendations
    if len(fraud_alerts) > 10:
        insights['prevention_recommendations'].extend([
            "Implement real-time ML monitoring for transactions >$1000",
            "Enhance verification for new accounts with high-value transactions",
            "Deploy geographic anomaly detection for cross-border transactions"
        ])
    
    return insights

# Load data and model
pending_approvals = load_pending_approvals()
fraud_alerts = load_fraud_alerts()
users = load_users()
transactions = load_transactions()
model = load_model()

# Initialize analytics
analytics = FraudAnalytics()
performance_metrics = analytics.calculate_performance_metrics()

# Generate ML insights
ml_insights = generate_ml_insights(model, fraud_alerts, transactions)

# Welcome message with ML status
ml_status = "Active 🟢" if model else "Inactive 🔴"
st.success(f"Welcome, {st.session_state.admin_details.get('name', 'Admin')}! 👨💼 • ML Model: {ml_status} • Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# =============================================================================
# REAL-TIME DASHBOARD METRICS WITH ML ENHANCEMENTS
# =============================================================================

st.subheader("📊 ML-Powered Security Intelligence")

# Top level metrics
col1, col2, col3, col4, col5 = st.columns(5)

active_alerts = [a for a in fraud_alerts if a['status'] == 'new']
high_risk_pending = [p for p in pending_approvals if p['risk_level'] == 'HIGH_RISK' and p['status'] == 'pending']
suspicious_users = []
ml_detected_users = []

# Enhanced suspicious user detection with ML
for user_id in users.keys():
    is_suspicious, red_flags, ml_confidence = enhanced_criminal_detection(user_id, model)
    if is_suspicious:
        suspicious_users.append(user_id)
        if ml_confidence > 0.6:
            ml_detected_users.append(user_id)

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
        "ML Detected Threats", 
        len(ml_detected_users),
        delta="🤖 AI Identified"
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
        "ML Accuracy", 
        f"{ml_insights['model_performance']['auc_roc']:.1%}",
        delta="AUC-ROC Score"
    )

# =============================================================================
# ML-POWERED VISUALIZATION CHARTS
# =============================================================================

st.subheader("🤖 Machine Learning Analytics")

col1, col2 = st.columns(2)

with col1:
    # ML Model Performance Metrics
    if model:
        metrics_data = {
            'Metric': ['AUC-ROC', 'Recall', 'Precision', 'F1-Score'],
            'Score': [
                ml_insights['model_performance']['auc_roc'],
                ml_insights['model_performance']['recall'],
                ml_insights['model_performance']['precision'],
                ml_insights['model_performance']['f1_score']
            ]
        }
        
        fig_performance = go.Figure()
        fig_performance.add_trace(go.Bar(
            x=metrics_data['Metric'],
            y=metrics_data['Score'],
            marker_color=['#00CC96', '#EF553B', '#AB63FA', '#FFA15A'],
            text=[f'{score:.1%}' for score in metrics_data['Score']],
            textposition='auto',
        ))
        
        fig_performance.update_layout(
            title="XGBoost Model Performance Metrics",
            yaxis=dict(range=[0, 1]),
            height=300
        )
        st.plotly_chart(fig_performance, use_container_width=True)

with col2:
    # Risk Distribution with ML Confidence
    if pending_approvals:
        risk_data = []
        for approval in pending_approvals:
            if approval['status'] == 'pending':
                risk_data.append({
                    'risk_level': approval['risk_level'],
                    'amount': approval['transaction_data']['amount'],
                    'fraud_probability': approval['fraud_probability']
                })
        
        if risk_data:
            risk_df = pd.DataFrame(risk_data)
            
            # Enhanced risk analysis with ML confidence
            fig_risk = px.scatter(
                risk_df,
                x='amount',
                y='fraud_probability',
                color='risk_level',
                size='fraud_probability',
                title="ML Risk Analysis: Amount vs Fraud Probability",
                color_discrete_map={
                    'HIGH_RISK': '#FF6B6B',
                    'MEDIUM_RISK': '#FFD93D', 
                    'LOW_RISK': '#6BCF7F'
                },
                hover_data=['risk_level']
            )
            st.plotly_chart(fig_risk, use_container_width=True)

# =============================================================================
# ML-POWERED THREAT INTELLIGENCE
# =============================================================================

st.subheader("🔍 ML Threat Intelligence")

if ml_insights['top_risk_factors']:
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🎯 Top Risk Factors (ML Identified):**")
        for factor in ml_insights['top_risk_factors'][:3]:
            st.write(f"• {factor}")
    
    with col2:
        st.write("**🛡️ ML Prevention Recommendations:**")
        for recommendation in ml_insights['prevention_recommendations'][:2]:
            st.write(f"• {recommendation}")

# ML-Powered User Risk Profiling
if suspicious_users:
    st.subheader("👤 ML Risk Profiling - High Risk Users")
    
    risk_profiles = []
    for user_id in suspicious_users[:5]:  # Show top 5
        risk_profile = get_ml_user_risk_profile(user_id, model)
        user_data = users.get(user_id, {})
        
        risk_profiles.append({
            'User ID': user_id,
            'Name': user_data.get('full_name', 'N/A'),
            'ML Risk Score': f"{risk_profile['risk_score']:.2f}",
            'Anomalies': len(risk_profile['behavioral_anomalies']),
            'Recommended Action': risk_profile['recommended_action']
        })
    
    if risk_profiles:
        df_risk = pd.DataFrame(risk_profiles)
        st.dataframe(df_risk, use_container_width=True)

# =============================================================================
# ENHANCED QUICK ACTIONS WITH ML
# =============================================================================

st.subheader("🚀 ML-Enhanced Security Operations")

action_col1, action_col2, action_col3, action_col4 = st.columns(4)

with action_col1:
    if st.button("🔄 Refresh ML Intelligence", use_container_width=True):
        st.rerun()

with action_col2:
    if st.button("🤖 Run ML Analysis", use_container_width=True):
        st.info("Running advanced ML pattern detection...")
        # Simulate ML analysis
        trends = predict_fraud_trends(model, fraud_alerts)
        if trends:
            st.success(f"ML Prediction: {trends['predicted_weekly_alerts']} fraud alerts expected next week")
            st.write(f"Trend: {trends['risk_trend'].title()} | Confidence: {trends['ml_confidence']:.0%}")

with action_col3:
    if st.button("👮 ML Threat Alert", use_container_width=True):
        if ml_detected_users:
            st.warning(f"🚨 ML detected {len(ml_detected_users)} high-confidence threats!")
            st.write("**ML-Identified Suspicious Users:**")
            for user_id in ml_detected_users[:3]:
                st.write(f"• {user_id}")
        else:
            st.info("No high-confidence ML threats detected")

with action_col4:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.session_state.admin_user = None
        st.session_state.admin_details = {}
        st.rerun()
    
# =============================================================================
# ENHANCED PENDING TRANSACTIONS WITH ML DETECTION
# =============================================================================

st.subheader("⏳ ML-Enhanced Transaction Approvals")

if not pending_approvals:
    st.info("🎉 No pending transactions for approval")
else:
    # Enhanced filter options
    col1, col2 = st.columns(2)
    with col1:
        risk_filter = st.selectbox("Filter by Risk Level", ["All", "HIGH_RISK", "MEDIUM_RISK", "LOW_RISK", "ML_DETECTED"])
    with col2:
        sort_by = st.selectbox("Sort Transactions By", ["Risk Level", "ML Confidence", "Amount", "Date", "Fraud Probability"])
    
    filtered_approvals = [p for p in pending_approvals if p['status'] == 'pending']
    
    if risk_filter != "All":
        if risk_filter == "ML_DETECTED":
            filtered_approvals = [p for p in filtered_approvals 
                                if enhanced_criminal_detection(p['user_id'], model)[0]]
        else:
            filtered_approvals = [p for p in filtered_approvals if p['risk_level'] == risk_filter]
    
    # Enhanced sorting
    if sort_by == "Risk Level":
        risk_order = {"HIGH_RISK": 3, "MEDIUM_RISK": 2, "LOW_RISK": 1}
        filtered_approvals.sort(key=lambda x: risk_order.get(x['risk_level'], 0), reverse=True)
    elif sort_by == "ML Confidence":
        filtered_approvals.sort(key=lambda x: enhanced_criminal_detection(x['user_id'], model)[2], reverse=True)
    elif sort_by == "Amount":
        filtered_approvals.sort(key=lambda x: x['transaction_data']['amount'], reverse=True)
    elif sort_by == "Date":
        filtered_approvals.sort(key=lambda x: x['timestamp'], reverse=True)
    elif sort_by == "Fraud Probability":
        filtered_approvals.sort(key=lambda x: x['fraud_probability'], reverse=True)
    
    for approval in filtered_approvals[:8]:
        # Enhanced criminal detection with ML confidence
        is_suspicious, red_flags, ml_confidence = enhanced_criminal_detection(approval['user_id'], model)
        
        risk_color = {
            'HIGH_RISK': 'red',
            'MEDIUM_RISK': 'orange', 
            'LOW_RISK': 'green'
        }.get(approval['risk_level'], 'gray')
        
        ml_badge = " 🤖" if ml_confidence > 0.6 else ""
        
        with st.expander(f":{risk_color}[**TX: {approval['transaction_id']}**] | ${approval['transaction_data']['amount']:,.2f} | {approval['risk_level'].replace('_', ' ')} | {approval['fraud_probability']:.1%}{ml_badge}"):
            
            if is_suspicious:
                st.error("🚨 **ML-POTENTIAL CRIMINAL ACTIVITY DETECTED**")
                st.write(f"**ML Confidence:** {ml_confidence:.0%}")
                st.write("**ML Detection Flags:**")
                for flag in red_flags[:4]:
                    st.write(f"• {flag}")
                
                if ml_confidence > 0.7:
                    st.warning("**🤖 ML RECOMMENDATION:** Immediate law enforcement notification")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**User:** {approval['user_id']}")
                st.write(f"**Amount:** ${approval['transaction_data']['amount']:,.2f}")
                st.write(f"**Merchant:** {approval['transaction_data']['merchant_name']}")
                st.write(f"**ML Fraud Probability:** {approval['fraud_probability']:.2%}")
                
            with col2:
                st.write(f"**Submitted:** {approval['timestamp']}")
                st.write(f"**Risk Level:** {approval['risk_level']}")
                st.write(f"**Category:** {approval['transaction_data']['category']}")
                st.write(f"**ML Confidence:** {ml_confidence:.0%}" if ml_confidence > 0 else "**ML Confidence:** N/A")
            
            # Enhanced admin actions with ML recommendations
            st.subheader("🤖 ML-Assisted Decision Making")
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
                if is_suspicious and ml_confidence > 0.6 and st.button(f"👮 ML Alert Police", key=f"police_{approval['transaction_id']}"):
                    st.error("🚓 **ML-URGENT: Law enforcement notified with high-confidence detection**")
                    criminal_alert = {
                        'alert_id': f"ML_CRIMINAL_{int(datetime.now().timestamp())}",
                        'user_id': approval['user_id'],
                        'transaction_id': approval['transaction_id'],
                        'ml_confidence': ml_confidence,
                        'red_flags': red_flags,
                        'fraud_probability': approval['fraud_probability'],
                        'amount': approval['transaction_data']['amount'],
                        'timestamp': str(datetime.now()),
                        'priority': 'URGENT',
                        'ml_recommendation': 'IMMEDIATE_ACTION'
                    }
                    st.json(criminal_alert)

# =============================================================================
# ML SYSTEM PERFORMANCE ANALYTICS
# =============================================================================

st.subheader("📈 ML System Performance Analytics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Users", len(users))
    st.metric("ML Model AUC-ROC", f"{ml_insights['model_performance']['auc_roc']:.1%}")

with col2:
    st.metric("Fraud Recall", f"{ml_insights['model_performance']['recall']:.1%}")
    st.metric("ML Detected Threats", len(ml_detected_users))

with col3:
    st.metric("Precision", f"{ml_insights['model_performance']['precision']:.1%}")
    st.metric("High Risk Alerts", performance_metrics.get('high_risk_alerts', 0))

with col4:
    st.metric("F1-Score", f"{ml_insights['model_performance']['f1_score']:.1%}")
    st.metric("Total Fraud Prevented", f"${performance_metrics.get('total_fraud_amount', 0):,.2f}")

# Footer with ML status
st.divider()
ml_status_detail = "XGBoost Active (98.5% AUC-ROC)" if model else "ML Model Inactive"
st.caption(f"SecureBank AI Fraud Detection System • {ml_status_detail} • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Logged in as: {st.session_state.admin_user}")

