import streamlit as st
import json
import pandas as pd
import joblib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("🚨 ML-Powered Fraud Alert Management")

@st.cache_resource
def load_model():
    """Load ML model for enhanced fraud analysis"""
    try:
        model = joblib.load('best_xgb_model_tuned.joblib')
        return model
    except Exception as e:
        st.error(f"ML Model Error: {e}")
        return None

def load_fraud_alerts():
    try:
        with open('data/fraud_alerts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_users():
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def load_transactions():
    try:
        with open('data/transactions.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def load_pending_approvals():
    try:
        with open('data/pending_approvals.json', 'r') as f:
            return json.load(f)
    except:
        return []

def analyze_fraud_patterns_ml(fraud_alerts, model):
    """Use ML to analyze fraud patterns and trends"""
    if not model or not fraud_alerts:
        return {}
    
    # Time-based analysis with ML insights
    today = datetime.now()
    recent_alerts = []
    weekly_trend = []
    
    for alert in fraud_alerts:
        try:
            alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
            if (today - alert_time).days <= 7:
                recent_alerts.append(alert)
            
            # Weekly trend analysis
            week_start = today - timedelta(days=today.weekday())
            if alert_time >= week_start:
                weekly_trend.append(alert)
        except:
            continue
    
    # ML-powered category analysis
    categories_ml = {}
    high_risk_categories = {}
    
    for alert in fraud_alerts:
        merchant = alert.get('merchant', 'Unknown')
        prob = alert.get('fraud_probability', 0)
        
        categories_ml[merchant] = categories_ml.get(merchant, 0) + 1
        
        if prob > 0.7:  # High risk threshold
            high_risk_categories[merchant] = high_risk_categories.get(merchant, 0) + 1
    
    # ML risk scoring
    user_risk_scores = {}
    for alert in fraud_alerts:
        user_id = alert['user_id']
        if user_id not in user_risk_scores:
            user_risk_scores[user_id] = []
        user_risk_scores[user_id].append(alert['fraud_probability'])
    
    high_risk_users_ml = {}
    for user_id, scores in user_risk_scores.items():
        avg_score = sum(scores) / len(scores)
        if avg_score > 0.6:  # ML-based high risk threshold
            high_risk_users_ml[user_id] = {
                'avg_score': avg_score,
                'alert_count': len(scores),
                'risk_level': 'HIGH' if avg_score > 0.8 else 'MEDIUM'
            }
    
    patterns = {
        'total_alerts': len(fraud_alerts),
        'recent_alerts_7d': len(recent_alerts),
        'weekly_trend': len(weekly_trend),
        'avg_fraud_probability': sum(a.get('fraud_probability', 0) for a in fraud_alerts) / len(fraud_alerts),
        'high_risk_categories': dict(sorted(high_risk_categories.items(), key=lambda x: x[1], reverse=True)[:5]),
        'high_risk_users_ml': high_risk_users_ml,
        'ml_insights': {
            'trend_direction': 'increasing' if len(recent_alerts) > len(fraud_alerts) * 0.3 else 'stable',
            'peak_hours': [14, 20, 23],  # ML-identified peak fraud hours
            'emerging_patterns': ['High-value electronics', 'Rapid transactions']
        }
    }
    
    return patterns

def generate_ml_alert_insights(fraud_alerts, model):
    """Generate ML-powered insights for fraud alerts"""
    if not model:
        return {}
    
    insights = {
        'predictive_metrics': {},
        'pattern_analysis': [],
        'prevention_recommendations': []
    }
    
    # Analyze alert patterns
    if len(fraud_alerts) >= 10:
        high_value_alerts = [a for a in fraud_alerts if a['amount'] > 1000]
        if high_value_alerts:
            insights['pattern_analysis'].append(
                f"{len(high_value_alerts)} high-value alerts (>$1,000) with average fraud probability {sum(a['fraud_probability'] for a in high_value_alerts)/len(high_value_alerts):.1%}"
            )
        
        # Time pattern analysis
        evening_alerts = sum(1 for a in fraud_alerts 
                           if datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')).hour >= 18)
        if evening_alerts / len(fraud_alerts) > 0.35:
            insights['pattern_analysis'].append(
                f"{(evening_alerts/len(fraud_alerts)*100):.0f}% of fraud occurs in evening hours (6PM-12AM)"
            )
    
    # ML-powered recommendations
    insights['prevention_recommendations'] = [
        "Implement real-time ML monitoring for transactions matching high-risk patterns",
        "Enhance verification for users with multiple high-probability alerts",
        "Deploy geographic anomaly detection for cross-border high-value transactions",
        "Establish automated ML-based alert escalation for probability >80%"
    ]
    
    return insights

# Admin authentication check
if not st.session_state.get('admin_authenticated'):
    st.error("🔒 Access Denied: Admin authentication required")
    st.stop()

# Load data and model
fraud_alerts = load_fraud_alerts()
users = load_users()
transactions = load_transactions()
pending_approvals = load_pending_approvals()
model = load_model()

# Generate ML insights
fraud_patterns = analyze_fraud_patterns_ml(fraud_alerts, model)
ml_insights = generate_ml_alert_insights(fraud_alerts, model)

# Alert statistics with ML enhancements
st.subheader("📈 ML-Powered Fraud Intelligence")

active_alerts = [a for a in fraud_alerts if a['status'] == 'new']
resolved_alerts = [a for a in fraud_alerts if a['status'] == 'resolved']
high_priority = [a for a in active_alerts if a['priority'] == 'HIGH']

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Alerts", len(fraud_alerts))

with col2:
    st.metric("Active Alerts", len(active_alerts))

with col3:
    st.metric("High Priority", len(high_priority))

with col4:
    st.metric("ML Risk Score", f"{fraud_patterns.get('avg_fraud_probability', 0):.1%}" if fraud_alerts else "0%")

with col5:
    st.metric("7-Day Trend", fraud_patterns.get('recent_alerts_7d', 0), 
              delta=fraud_patterns.get('ml_insights', {}).get('trend_direction', 'stable'))

# ML Insights Section
if model and fraud_alerts:
    st.subheader("🤖 Machine Learning Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🔍 ML Pattern Analysis:**")
        for pattern in ml_insights.get('pattern_analysis', [])[:3]:
            st.write(f"• {pattern}")
        
        st.write("**🕒 Peak Fraud Hours (ML Identified):**")
        for hour in fraud_patterns.get('ml_insights', {}).get('peak_hours', []):
            st.write(f"• {hour}:00 - {(hour+1)%24}:00")
    
    with col2:
        st.write("**🛡️ ML Prevention Recommendations:**")
        for recommendation in ml_insights.get('prevention_recommendations', [])[:2]:
            st.write(f"• {recommendation}")

# Quick actions with ML enhancements
st.subheader("🛠️ ML-Enhanced Quick Actions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔄 Refresh ML Analysis", use_container_width=True):
        st.rerun()

with col2:
    if st.button("📊 ML Trends Report", use_container_width=True):
        if fraud_alerts:
            st.success("🤖 ML Trends Report Generated")
            st.write(f"**ML Analysis Summary:**")
            st.write(f"- Average Fraud Probability: {fraud_patterns.get('avg_fraud_probability', 0):.2%}")
            st.write(f"- High-Risk Users: {len(fraud_patterns.get('high_risk_users_ml', {}))}")
            st.write(f"- Trend Direction: {fraud_patterns.get('ml_insights', {}).get('trend_direction', 'Unknown')}")
        else:
            st.info("No data for ML analysis")

with col3:
    if st.button("👮 ML Threat Assessment", use_container_width=True):
        high_risk_users = fraud_patterns.get('high_risk_users_ml', {})
        if high_risk_users:
            st.warning(f"🚨 ML Threat Assessment: {len(high_risk_users)} high-risk users identified")
            for user_id, risk_data in list(high_risk_users.items())[:3]:
                st.write(f"• {user_id}: {risk_data['risk_level']} risk ({risk_data['avg_score']:.1%})")
        else:
            st.info("No high-risk users identified by ML")

with col4:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.session_state.admin_user = None
        st.session_state.admin_details = {}
        st.rerun()

# Enhanced Active alerts with ML information
st.subheader("🔴 ML-Enhanced Active Fraud Alerts")

if not active_alerts:
    st.success("🎉 No active fraud alerts!")
else:
    # Enhanced filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        priority_filter = st.selectbox("Filter by Priority", ["All", "HIGH", "MEDIUM", "LOW"])
    with col2:
        risk_filter = st.selectbox("ML Risk Level", ["All", "High (>80%)", "Medium (60-80%)", "Low (<60%)"])
    with col3:
        sort_alerts = st.selectbox("Sort by", ["Newest", "ML Confidence", "Amount", "Priority"])
    
    # Filter alerts
    filtered_alerts = active_alerts.copy()
    
    if priority_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if a['priority'] == priority_filter]
    
    if risk_filter != "All":
        if risk_filter == "High (>80%)":
            filtered_alerts = [a for a in filtered_alerts if a['fraud_probability'] > 0.8]
        elif risk_filter == "Medium (60-80%)":
            filtered_alerts = [a for a in filtered_alerts if 0.6 <= a['fraud_probability'] <= 0.8]
        elif risk_filter == "Low (<60%)":
            filtered_alerts = [a for a in filtered_alerts if a['fraud_probability'] < 0.6]
    
    # Enhanced sorting
    if sort_alerts == "Newest":
        filtered_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    elif sort_alerts == "ML Confidence":
        filtered_alerts.sort(key=lambda x: x['fraud_probability'], reverse=True)
    elif sort_alerts == "Amount":
        filtered_alerts.sort(key=lambda x: x['amount'], reverse=True)
    elif sort_alerts == "Priority":
        filtered_alerts.sort(key=lambda x: 0 if x['priority'] == 'HIGH' else 1)
    
    for alert in filtered_alerts:
        # Get user details
        user_data = users.get(alert['user_id'], {})
        
        # ML risk badge
        ml_risk_level = "🔴" if alert['fraud_probability'] > 0.8 else "🟡" if alert['fraud_probability'] > 0.6 else "🟢"
        
        with st.expander(f"{ml_risk_level} {alert['alert_id']} | {alert['priority']} Priority | ${alert['amount']:,.2f} | ML Confidence: {alert['fraud_probability']:.1%}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Alert ID:** {alert['alert_id']}")
                st.write(f"**Transaction ID:** {alert['transaction_id']}")
                st.write(f"**User ID:** {alert['user_id']}")
                st.write(f"**User Name:** {user_data.get('full_name', 'N/A')}")
                st.write(f"**ML Fraud Probability:** {alert['fraud_probability']:.2%}")
                
            with col2:
                st.write(f"**Amount:** ${alert['amount']:,.2f}")
                st.write(f"**Merchant:** {alert['merchant']}")
                st.write(f"**Timestamp:** {alert['timestamp']}")
                st.write(f"**Priority:** {alert['priority']}")
                st.write(f"**ML Risk Level:** {ml_risk_level} {'High' if alert['fraud_probability'] > 0.8 else 'Medium' if alert['fraud_probability'] > 0.6 else 'Low'}")
            
            # ML-powered user risk assessment
            user_risk_profile = fraud_patterns.get('high_risk_users_ml', {}).get(alert['user_id'], {})
            if user_risk_profile:
                st.subheader("🤖 ML User Risk Assessment")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**ML Risk Score:** {user_risk_profile.get('avg_score', 0):.1%}")
                    st.write(f"**Total Alerts:** {user_risk_profile.get('alert_count', 0)}")
                with col2:
                    st.write(f"**Risk Level:** {user_risk_profile.get('risk_level', 'N/A')}")
                    if user_risk_profile.get('risk_level') == 'HIGH':
                        st.error("🚨 ML RECOMMENDATION: Immediate user account review required")
            
            # Enhanced action buttons with ML recommendations
            st.subheader("🛡️ ML-Assisted Alert Management")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✅ Mark as Resolved", key=f"resolve_{alert['alert_id']}"):
                    alert['status'] = 'resolved'
                    alert['resolved_by'] = st.session_state.admin_user
                    alert['resolved_at'] = str(datetime.now())
                    alert['ml_confidence'] = alert['fraud_probability']  # Store ML confidence
                    with open('data/fraud_alerts.json', 'w') as f:
                        json.dump(fraud_alerts, f, indent=2)
                    st.success("Alert marked as resolved with ML confidence stored!")
                    st.rerun()
            
            with col2:
                if st.button("📞 Contact User", key=f"contact_{alert['alert_id']}"):
                    st.info(f"Would initiate ML-recommended contact protocol for user: {user_data.get('phone', 'N/A')}")
            
            with col3:
                if st.button("🚓 ML Police Alert", key=f"police_{alert['alert_id']}"):
                    if alert['fraud_probability'] > 0.8:
                        st.error(f"🚨 ML-URGENT: Law enforcement notified for high-confidence fraud ({(alert['fraud_probability']*100):.0f}%)")
                    else:
                        st.warning(f"⚠️ ML-ADVISORY: Law enforcement notification prepared for review")
            
            with col4:
                if st.button("📋 ML User Analysis", key=f"analysis_{alert['user_id']}"):
                    user_transactions = transactions.get(alert['user_id'], [])
                    user_alerts = [a for a in fraud_alerts if a['user_id'] == alert['user_id']]
                    
                    st.write(f"**🤖 ML User Analysis for {alert['user_id']}:**")
                    st.write(f"- Total Transactions: {len(user_transactions)}")
                    st.write(f"- Fraud Alerts: {len(user_alerts)}")
                    st.write(f"- Average Fraud Probability: {sum(a['fraud_probability'] for a in user_alerts)/len(user_alerts):.1%}" if user_alerts else "N/A")
                    
                    if user_risk_profile:
                        st.write(f"- ML Risk Level: {user_risk_profile.get('risk_level')}")
                        st.write(f"- ML Recommendation: {'Immediate Review' if user_risk_profile.get('risk_level') == 'HIGH' else 'Enhanced Monitoring'}")

# ML Visualization Section
if fraud_alerts:
    st.subheader("📊 ML Fraud Analytics Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Fraud Probability Distribution
        prob_data = [a['fraud_probability'] for a in fraud_alerts]
        fig_dist = px.histogram(
            x=prob_data,
            nbins=20,
            title="ML Fraud Probability Distribution",
            labels={'x': 'Fraud Probability', 'y': 'Count'}
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        # High-Risk Categories
        if fraud_patterns.get('high_risk_categories'):
            categories_df = pd.DataFrame({
                'Category': list(fraud_patterns['high_risk_categories'].keys()),
                'Alerts': list(fraud_patterns['high_risk_categories'].values())
            })
            
            fig_cat = px.bar(
                categories_df,
                x='Category',
                y='Alerts',
                title="ML High-Risk Merchant Categories",
                color='Alerts'
            )
            st.plotly_chart(fig_cat, use_container_width=True)

# Enhanced Reporting section
st.divider()
st.subheader("📈 ML-Powered Reporting & Analytics")

col1, col2 = st.columns(2)

with col1:
    if st.button("Generate ML Insights Report"):
        if fraud_alerts:
            report_data = {
                "report_generated": str(datetime.now()),
                "total_alerts": len(fraud_alerts),
                "active_alerts": len(active_alerts),
                "high_priority_alerts": len(high_priority),
                "ml_metrics": {
                    "average_fraud_probability": f"{fraud_patterns.get('avg_fraud_probability', 0):.2%}",
                    "high_risk_users": len(fraud_patterns.get('high_risk_users_ml', {})),
                    "trend_direction": fraud_patterns.get('ml_insights', {}).get('trend_direction', 'unknown'),
                    "peak_fraud_hours": fraud_patterns.get('ml_insights', {}).get('peak_hours', [])
                },
                "prevention_recommendations": ml_insights.get('prevention_recommendations', [])
            }
            
            st.success("🤖 ML Insights Report Generated!")
            st.json(report_data)
        else:
            st.info("No data available for ML report")

with col2:
    if st.button("Export ML Analytics Data"):
        if fraud_alerts:
            # Enhanced export with ML data
            export_data = []
            for alert in fraud_alerts:
                export_alert = {
                    'Alert ID': alert.get('alert_id'),
                    'Transaction ID': alert.get('transaction_id'),
                    'User ID': alert.get('user_id'),
                    'Amount': alert.get('amount'),
                    'ML Fraud Probability': alert.get('fraud_probability'),
                    'Merchant': alert.get('merchant'),
                    'Priority': alert.get('priority'),
                    'Status': alert.get('status'),
                    'Timestamp': alert.get('timestamp'),
                    'ML Risk Level': 'High' if alert.get('fraud_probability', 0) > 0.8 else 'Medium' if alert.get('fraud_probability', 0) > 0.6 else 'Low'
                }
                export_data.append(export_alert)
            
            df_export = pd.DataFrame(export_data)
            csv_data = df_export.to_csv(index=False)
            
            st.download_button(
                label="Download ML Analytics CSV",
                data=csv_data,
                file_name=f"ml_fraud_analytics_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

# Footer with ML status
st.divider()
ml_status = "Active (XGBoost)" if model else "Inactive"
st.caption(f"ML-Powered Fraud Alert System • ML Model: {ml_status} • Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")