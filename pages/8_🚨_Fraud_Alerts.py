import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter
import numpy as np

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("🚨 Hybrid ML-Powered Fraud Alert Management")

from hybrid_model_manager import get_hybrid_prediction

def load_hybrid_model():
    """Load hybrid model system"""
    try:
        # Test hybrid system
        test_result = get_hybrid_prediction(
            {'amount': 100}, 
            {}, 
            6.9271, 
            79.8612
        )
        print("✅ Hybrid model system loaded successfully")
        return True
    except Exception as e:
        st.error(f"❌ Hybrid model loading error: {e}")
        return False

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

def calculate_real_peak_hours(fraud_alerts):
    """Calculate actual peak fraud hours from data"""
    if not fraud_alerts:
        return []
    
    hours = []
    for alert in fraud_alerts:
        try:
            alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
            hours.append(alert_time.hour)
        except:
            continue
    
    hour_counts = Counter(hours)
    return [hour for hour, count in hour_counts.most_common(3)]

def analyze_geographic_patterns(fraud_alerts):
    """Detect geographic clustering in fraud alerts"""
    if not fraud_alerts:
        return []
    
    locations = []
    for alert in fraud_alerts:
        if 'transaction_data' in alert:
            tx_data = alert['transaction_data']
            if tx_data.get('merch_lat') and tx_data.get('merch_lon'):
                lat_round = round(tx_data['merch_lat'], 1)
                lon_round = round(tx_data['merch_lon'], 1)
                locations.append((lat_round, lon_round))
    
    location_counts = Counter(locations)
    clusters = [loc for loc, count in location_counts.most_common(3) if count >= 2]
    return clusters

def analyze_merchant_patterns(fraud_alerts):
    """Analyze merchant-specific fraud patterns"""
    if not fraud_alerts:
        return []
    
    patterns = []
    
    merchants = []
    for alert in fraud_alerts:
        merchant = alert.get('merchant', 'Unknown')
        merchants.append(merchant)
    
    merchant_counts = Counter(merchants)
    top_merchants = [merchant for merchant, count in merchant_counts.most_common(3) if count >= 2]
    
    for merchant in top_merchants:
        patterns.append(f"Recurring fraud at {merchant}")
    
    return patterns

def analyze_temporal_patterns(fraud_alerts):
    """Analyze time-based fraud patterns"""
    if not fraud_alerts:
        return []
    
    patterns = []
    
    weekdays = []
    for alert in fraud_alerts:
        try:
            alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
            weekdays.append(alert_time.weekday())
        except:
            continue
    
    if weekdays:
        weekday_counts = Counter(weekdays)
        most_common_day = weekday_counts.most_common(1)[0][0]
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        patterns.append(f"Peak fraud on {day_names[most_common_day]}")
    
    if len(fraud_alerts) >= 3:
        timestamps = []
        for alert in fraud_alerts:
            try:
                alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
                timestamps.append(alert_time)
            except:
                continue
        
        timestamps.sort()
        rapid_count = 0
        for i in range(1, len(timestamps)):
            time_diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 60
            if time_diff < 5:
                rapid_count += 1
        
        if rapid_count >= 2:
            patterns.append(f"Rapid succession pattern ({rapid_count} instances)")
    
    return patterns

def detect_emerging_patterns(fraud_alerts):
    """Detect actual emerging fraud patterns from data"""
    patterns = []
    
    if not fraud_alerts:
        return patterns
    
    high_value_alerts = [a for a in fraud_alerts if a['amount'] > 1000]
    high_value_ratio = len(high_value_alerts) / len(fraud_alerts)
    if high_value_ratio > 0.3:
        patterns.append(f"High-value fraud concentration ({high_value_ratio:.1%} > $1000)")
    
    high_confidence_alerts = [a for a in fraud_alerts if a['fraud_probability'] > 0.8]
    if len(high_confidence_alerts) >= 3:
        patterns.append(f"High-confidence fraud cluster ({len(high_confidence_alerts)} alerts > 80%)")
    
    geo_clusters = analyze_geographic_patterns(fraud_alerts)
    if geo_clusters:
        patterns.append(f"Geographic clustering ({len(geo_clusters)} locations)")
    
    temp_patterns = analyze_temporal_patterns(fraud_alerts)
    patterns.extend(temp_patterns)
    
    merchant_patterns = analyze_merchant_patterns(fraud_alerts)
    patterns.extend(merchant_patterns)
    
    return patterns[:4]

def calculate_trend_direction(fraud_alerts):
    """Calculate actual trend direction from recent data"""
    if len(fraud_alerts) < 10:
        return 'insufficient_data'
    
    today = datetime.now()
    two_weeks_ago = today - timedelta(days=14)
    one_week_ago = today - timedelta(days=7)
    
    alerts_2w_1w = 0
    alerts_1w_now = 0
    
    for alert in fraud_alerts:
        try:
            alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
            if two_weeks_ago <= alert_time < one_week_ago:
                alerts_2w_1w += 1
            elif one_week_ago <= alert_time <= today:
                alerts_1w_now += 1
        except:
            continue
    
    if alerts_2w_1w == 0:
        return 'insufficient_data'
    
    growth_ratio = alerts_1w_now / alerts_2w_1w
    
    if growth_ratio > 1.3:
        return 'increasing'
    elif growth_ratio < 0.7:
        return 'decreasing'
    else:
        return 'stable'

def analyze_fraud_patterns_hybrid_ml(fraud_alerts):
    """Use Hybrid ML to analyze fraud patterns and trends"""
    if not fraud_alerts:
        return {
            'total_alerts': 0,
            'recent_alerts_7d': 0,
            'avg_fraud_probability': 0,
            'high_risk_categories': {},
            'high_risk_users_ml': {},
            'hybrid_ml_insights': {
                'trend_direction': 'insufficient_data',
                'peak_hours': [],
                'emerging_patterns': []
            }
        }
    
    today = datetime.now()
    recent_alerts = []
    weekly_trend = []
    
    for alert in fraud_alerts:
        try:
            alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
            if (today - alert_time).days <= 7:
                recent_alerts.append(alert)
            
            week_start = today - timedelta(days=today.weekday())
            if alert_time >= week_start:
                weekly_trend.append(alert)
        except:
            continue
    
    categories_ml = {}
    high_risk_categories = {}
    
    for alert in fraud_alerts:
        merchant = alert.get('merchant', 'Unknown')
        prob = alert.get('fraud_probability', 0)
        
        categories_ml[merchant] = categories_ml.get(merchant, 0) + 1
        
        if prob > 0.7:
            high_risk_categories[merchant] = high_risk_categories.get(merchant, 0) + 1
    
    user_risk_scores = {}
    for alert in fraud_alerts:
        user_id = alert['user_id']
        if user_id not in user_risk_scores:
            user_risk_scores[user_id] = []
        user_risk_scores[user_id].append(alert['fraud_probability'])
    
    high_risk_users_ml = {}
    for user_id, scores in user_risk_scores.items():
        avg_score = sum(scores) / len(scores)
        if avg_score > 0.6:
            high_risk_users_ml[user_id] = {
                'avg_score': avg_score,
                'alert_count': len(scores),
                'risk_level': 'HIGH' if avg_score > 0.8 else 'MEDIUM'
            }
    
    peak_hours = calculate_real_peak_hours(fraud_alerts)
    emerging_patterns = detect_emerging_patterns(fraud_alerts)
    trend_direction = calculate_trend_direction(fraud_alerts)
    
    patterns = {
        'total_alerts': len(fraud_alerts),
        'recent_alerts_7d': len(recent_alerts),
        'weekly_trend': len(weekly_trend),
        'avg_fraud_probability': sum(a.get('fraud_probability', 0) for a in fraud_alerts) / len(fraud_alerts),
        'high_risk_categories': dict(sorted(high_risk_categories.items(), key=lambda x: x[1], reverse=True)[:5]),
        'high_risk_users_ml': high_risk_users_ml,
        'hybrid_ml_insights': {
            'trend_direction': trend_direction,
            'peak_hours': peak_hours,
            'emerging_patterns': emerging_patterns
        }
    }
    
    return patterns

def generate_hybrid_ml_alert_insights(fraud_alerts):
    """Generate Hybrid ML-powered insights for fraud alerts"""
    if not fraud_alerts:
        return {
            'predictive_metrics': {},
            'pattern_analysis': [],
            'prevention_recommendations': []
        }
    
    insights = {
        'predictive_metrics': {},
        'pattern_analysis': [],
        'prevention_recommendations': []
    }
    
    if len(fraud_alerts) >= 5:
        high_value_alerts = [a for a in fraud_alerts if a['amount'] > 1000]
        if high_value_alerts:
            avg_high_value_prob = sum(a['fraud_probability'] for a in high_value_alerts) / len(high_value_alerts)
            insights['pattern_analysis'].append(
                f"{len(high_value_alerts)} high-value alerts (>$1,000) with average fraud probability {avg_high_value_prob:.1%}"
            )
        
        evening_alerts = 0
        night_alerts = 0
        for alert in fraud_alerts:
            try:
                alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
                hour = alert_time.hour
                if 18 <= hour < 24:
                    evening_alerts += 1
                elif 0 <= hour < 6:
                    night_alerts += 1
            except:
                continue
        
        total_alerts = len(fraud_alerts)
        if total_alerts > 0:
            evening_pct = (evening_alerts / total_alerts) * 100
            night_pct = (night_alerts / total_alerts) * 100
            
            if evening_pct > 35:
                insights['pattern_analysis'].append(f"Evening concentration: {evening_pct:.0f}% of fraud (6PM-12AM)")
            if night_pct > 20:
                insights['pattern_analysis'].append(f"Night activity: {night_pct:.0f}% of fraud (12AM-6AM)")
        
        user_alert_counts = {}
        for alert in fraud_alerts:
            user_id = alert['user_id']
            user_alert_counts[user_id] = user_alert_counts.get(user_id, 0) + 1
        
        repeat_offenders = [user_id for user_id, count in user_alert_counts.items() if count >= 3]
        if repeat_offenders:
            insights['pattern_analysis'].append(f"Repeat offenders: {len(repeat_offenders)} users with 3+ alerts")
    
    prevention_recommendations = []
    
    high_value_count = len([a for a in fraud_alerts if a['amount'] > 1000])
    if high_value_count / len(fraud_alerts) > 0.25:
        prevention_recommendations.append("Implement enhanced verification for transactions >$1000")
    
    geo_clusters = analyze_geographic_patterns(fraud_alerts)
    if geo_clusters:
        prevention_recommendations.append("Deploy geographic anomaly detection for identified clusters")
    
    rapid_patterns = [p for p in detect_emerging_patterns(fraud_alerts) if "rapid succession" in p.lower()]
    if rapid_patterns:
        prevention_recommendations.append("Establish velocity checks for rapid transaction sequences")
    
    prevention_recommendations.extend([
        "Implement real-time hybrid ML monitoring for high-risk transaction patterns",
        "Enhance verification for users with multiple high-probability alerts",
        "Establish automated hybrid ML-based alert escalation for probability >80%"
    ])
    
    insights['prevention_recommendations'] = prevention_recommendations[:4]
    
    return insights

def generate_risk_heatmap_data(fraud_alerts):
    """Generate data for fraud risk heatmap"""
    if not fraud_alerts:
        return []
    
    heatmap_data = []
    for alert in fraud_alerts:
        if 'transaction_data' in alert:
            tx_data = alert['transaction_data']
            if tx_data.get('merch_lat') and tx_data.get('merch_lon'):
                heatmap_data.append({
                    'lat': tx_data['merch_lat'],
                    'lon': tx_data['merch_lon'],
                    'risk': alert['fraud_probability'],
                    'amount': alert['amount'],
                    'merchant': alert.get('merchant', 'Unknown'),
                    'risk_level': alert.get('risk_level', 'MEDIUM_RISK')
                })
    
    return heatmap_data

def resolve_fraud_alert(alert_id, resolved_by):
    """Resolve a fraud alert"""
    try:
        fraud_alerts = load_fraud_alerts()
        for alert in fraud_alerts:
            if alert['alert_id'] == alert_id:
                alert['status'] = 'resolved'
                alert['resolved_by'] = resolved_by
                alert['resolved_at'] = str(datetime.now())
                break
        
        with open('data/fraud_alerts.json', 'w') as f:
            json.dump(fraud_alerts, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error resolving alert: {e}")
        return False

# Admin authentication check
if not st.session_state.get('admin_authenticated'):
    st.error("🔒 Access Denied: Admin authentication required")
    st.stop()

# Load data and hybrid model
fraud_alerts = load_fraud_alerts()
users = load_users()
transactions = load_transactions()
pending_approvals = load_pending_approvals()
hybrid_model_loaded = load_hybrid_model()

# Generate Hybrid ML insights
fraud_patterns = analyze_fraud_patterns_hybrid_ml(fraud_alerts)
hybrid_ml_insights = generate_hybrid_ml_alert_insights(fraud_alerts)

# Alert statistics with Hybrid ML enhancements
st.subheader("📈 Hybrid ML-Powered Fraud Intelligence")

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
    avg_prob = fraud_patterns.get('avg_fraud_probability', 0)
    st.metric("Hybrid ML Risk Score", f"{avg_prob:.1%}" if fraud_alerts else "0%")

with col5:
    trend = fraud_patterns.get('hybrid_ml_insights', {}).get('trend_direction', 'stable')
    trend_icon = "📈" if trend == 'increasing' else "📉" if trend == 'decreasing' else "➡️"
    st.metric("7-Day Trend", fraud_patterns.get('recent_alerts_7d', 0), delta=trend_icon)

# Hybrid ML Insights Section
if hybrid_model_loaded and fraud_alerts:
    st.subheader("🤖 Hybrid Machine Learning Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🔍 Hybrid ML Pattern Analysis:**")
        patterns = hybrid_ml_insights.get('pattern_analysis', [])
        if patterns:
            for pattern in patterns[:3]:
                st.write(f"• {pattern}")
        else:
            st.write("• No significant patterns detected")
        
        st.write("**🕒 Peak Fraud Hours:**")
        peak_hours = fraud_patterns.get('hybrid_ml_insights', {}).get('peak_hours', [])
        if peak_hours:
            for hour in peak_hours:
                st.write(f"• {hour}:00 - {(hour+1)%24}:00")
        else:
            st.write("• Insufficient data for peak hour analysis")
    
    with col2:
        st.write("**🛡️ Hybrid ML Prevention Recommendations:**")
        recommendations = hybrid_ml_insights.get('prevention_recommendations', [])
        for recommendation in recommendations[:3]:
            st.write(f"• {recommendation}")
        
        emerging = fraud_patterns.get('hybrid_ml_insights', {}).get('emerging_patterns', [])
        if emerging:
            st.write("**🚨 Emerging Patterns:**")
            for pattern in emerging[:2]:
                st.write(f"• {pattern}")

# Hybrid ML System Information
st.subheader("🔧 Hybrid ML System Configuration")

col1, col2 = st.columns(2)

with col1:
    st.write("**🤖 Active Models:**")
    st.write("• 🇱🇰 **Sri Lanka Model**: Local transaction intelligence")
    st.write("• 🌍 **Original Model**: Global fraud patterns")
    st.write("• 🔄 **Smart Router**: Context-aware model selection")
    st.write(f"• ✅ **System Status**: {'Active 🟢' if hybrid_model_loaded else 'Inactive 🔴'}")

with col2:
    st.write("**📊 Performance Overview:**")
    st.write(f"• **Avg Fraud Probability**: {fraud_patterns.get('avg_fraud_probability', 0):.2%}")
    st.write(f"• **High-Risk Users**: {len(fraud_patterns.get('high_risk_users_ml', {}))}")
    st.write(f"• **Trend Direction**: {fraud_patterns.get('hybrid_ml_insights', {}).get('trend_direction', 'Unknown').title()}")
    st.write(f"• **Data Quality**: {'Excellent' if len(fraud_alerts) >= 20 else 'Good' if len(fraud_alerts) >= 10 else 'Limited'}")

# Quick actions with Hybrid ML enhancements
st.subheader("🛠️ Hybrid ML-Enhanced Quick Actions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔄 Refresh Hybrid Analysis", width='stretch'):
        st.rerun()

with col2:
    if st.button("📊 Hybrid ML Report", width='stretch'):
        if fraud_alerts:
            st.success("🤖 Hybrid ML Trends Report Generated")
            st.write(f"**Hybrid ML Analysis Summary:**")
            st.write(f"- Average Fraud Probability: {fraud_patterns.get('avg_fraud_probability', 0):.2%}")
            st.write(f"- High-Risk Users: {len(fraud_patterns.get('high_risk_users_ml', {}))}")
            st.write(f"- Trend Direction: {fraud_patterns.get('hybrid_ml_insights', {}).get('trend_direction', 'Unknown').title()}")
            
            peak_hours = fraud_patterns.get('hybrid_ml_insights', {}).get('peak_hours', [])
            if peak_hours:
                st.write(f"- Peak Fraud Hours: {', '.join(map(str, peak_hours))}:00")
        else:
            st.info("No data for hybrid ML analysis")

with col3:
    if st.button("👮 Hybrid Threat Assessment", width='stretch'):
        high_risk_users = fraud_patterns.get('high_risk_users_ml', {})
        if high_risk_users:
            st.warning(f"🚨 Hybrid ML Threat Assessment: {len(high_risk_users)} high-risk users identified")
            for user_id, risk_data in list(high_risk_users.items())[:3]:
                user_info = users.get(user_id, {})
                user_name = user_info.get('full_name', 'N/A')
                st.write(f"• {user_name} ({user_id}): {risk_data['risk_level']} risk ({risk_data['avg_score']:.1%})")
        else:
            st.info("No high-risk users identified by hybrid ML")

with col4:
    if st.button("🚪 Logout", width='stretch'):
        st.session_state.admin_authenticated = False
        st.session_state.admin_user = None
        st.session_state.admin_details = {}
        st.rerun()

# Enhanced Active alerts with Hybrid ML information
st.subheader("🔴 Hybrid ML-Enhanced Active Fraud Alerts")

if not active_alerts:
    st.success("🎉 No active fraud alerts!")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        priority_filter = st.selectbox("Filter by Priority", ["All", "HIGH", "MEDIUM", "LOW"])
    with col2:
        risk_filter = st.selectbox("Hybrid ML Risk Level", ["All", "High (>80%)", "Medium (60-80%)", "Low (<60%)"])
    with col3:
        sort_alerts = st.selectbox("Sort by", ["Newest", "ML Confidence", "Amount", "Priority"])
    
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
    
    if sort_alerts == "Newest":
        filtered_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    elif sort_alerts == "ML Confidence":
        filtered_alerts.sort(key=lambda x: x['fraud_probability'], reverse=True)
    elif sort_alerts == "Amount":
        filtered_alerts.sort(key=lambda x: x['amount'], reverse=True)
    elif sort_alerts == "Priority":
        filtered_alerts.sort(key=lambda x: 0 if x['priority'] == 'HIGH' else 1)
    
    for alert in filtered_alerts:
        user_data = users.get(alert['user_id'], {})
        
        ml_risk_level = "🔴" if alert['fraud_probability'] > 0.8 else "🟡" if alert['fraud_probability'] > 0.6 else "🟢"
        risk_level = alert.get('risk_level', 'MEDIUM_RISK')
        
        with st.expander(f"{ml_risk_level} {alert['alert_id']} | {alert['priority']} Priority | ${alert['amount']:,.2f} | Hybrid ML: {alert['fraud_probability']:.1%} | {risk_level.replace('_', ' ')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Alert ID:** {alert['alert_id']}")
                st.write(f"**Transaction ID:** {alert['transaction_id']}")
                st.write(f"**User ID:** {alert['user_id']}")
                st.write(f"**User Name:** {user_data.get('full_name', 'N/A')}")
                st.write(f"**Hybrid ML Fraud Probability:** {alert['fraud_probability']:.2%}")
                st.write(f"**Risk Level:** {risk_level.replace('_', ' ')}")
                
            with col2:
                st.write(f"**Amount:** ${alert['amount']:,.2f}")
                st.write(f"**Merchant:** {alert['merchant']}")
                st.write(f"**Timestamp:** {alert['timestamp']}")
                st.write(f"**Priority:** {alert['priority']}")
                st.write(f"**Hybrid ML Risk Level:** {ml_risk_level} {'High' if alert['fraud_probability'] > 0.8 else 'Medium' if alert['fraud_probability'] > 0.6 else 'Low'}")
            
            user_risk_profile = fraud_patterns.get('high_risk_users_ml', {}).get(alert['user_id'], {})
            if user_risk_profile:
                st.subheader("🤖 Hybrid ML User Risk Assessment")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**ML Risk Score:** {user_risk_profile.get('avg_score', 0):.1%}")
                    st.write(f"**Total Alerts:** {user_risk_profile.get('alert_count', 0)}")
                with col2:
                    st.write(f"**Risk Level:** {user_risk_profile.get('risk_level', 'N/A')}")
                    if user_risk_profile.get('risk_level') == 'HIGH':
                        st.error("🚨 HYBRID ML RECOMMENDATION: Immediate user account review required")
            
            # Action buttons
            st.subheader("🛡️ Alert Management")
            
            fraud_prob = alert['fraud_probability']
            if fraud_prob > 0.8:
                st.error("🚨 URGENT: High probability fraud detected by Hybrid ML")
            elif fraud_prob > 0.6:
                st.warning("⚠️ WARNING: Medium-high fraud probability detected")
            else:
                st.info("ℹ️ Moderate fraud probability - review recommended")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✅ Mark as Resolved", key=f"resolve_{alert['alert_id']}", width='stretch'):
                    if resolve_fraud_alert(alert['alert_id'], st.session_state.admin_user):
                        st.success("Alert marked as resolved!")
                        st.rerun()
            
            with col2:
                if st.button("📞 Contact User", key=f"contact_{alert['alert_id']}", width='stretch'):
                    st.info(f"Contact protocol initiated for user: {user_data.get('phone', 'N/A')}")
            
            with col3:
                if st.button("🚓 Police Alert", key=f"police_{alert['alert_id']}", width='stretch'):
                    if alert['fraud_probability'] > 0.8:
                        st.error(f"🚨 Law enforcement notified for high-confidence fraud ({(alert['fraud_probability']*100):.0f}%)")
                    else:
                        st.warning(f"⚠️ Law enforcement notification prepared for review")
            
            with col4:
                if st.button("📋 User Analysis", key=f"analysis_{alert['alert_id']}", width='stretch'):
                    user_transactions = transactions.get(alert['user_id'], [])
                    user_alerts = [a for a in fraud_alerts if a['user_id'] == alert['user_id']]
                    
                    st.write(f"**User Analysis for {alert['user_id']}:**")
                    st.write(f"- Total Transactions: {len(user_transactions)}")
                    st.write(f"- Fraud Alerts: {len(user_alerts)}")
                    if user_alerts:
                        st.write(f"- Average Fraud Probability: {sum(a['fraud_probability'] for a in user_alerts)/len(user_alerts):.1%}")
                    
                    if user_risk_profile:
                        st.write(f"- Hybrid ML Risk Level: {user_risk_profile.get('risk_level')}")

# Hybrid ML Visualization Section
if fraud_alerts:
    st.subheader("📊 Hybrid ML Fraud Analytics Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        prob_data = [a['fraud_probability'] for a in fraud_alerts]
        fig_dist = px.histogram(
            x=prob_data,
            nbins=20,
            title="Hybrid ML Fraud Probability Distribution",
            labels={'x': 'Fraud Probability', 'y': 'Count'},
            color_discrete_sequence=['#FF6B6B']
        )
        fig_dist.update_layout(showlegend=False)
        st.plotly_chart(fig_dist, config={'displayModeBar': False, 'responsive': True})
    
    with col2:
        if fraud_patterns.get('high_risk_categories'):
            categories_df = pd.DataFrame({
                'Merchant': list(fraud_patterns['high_risk_categories'].keys()),
                'High-Risk Alerts': list(fraud_patterns['high_risk_categories'].values())
            })
            
            fig_cat = px.bar(
                categories_df,
                x='Merchant',
                y='High-Risk Alerts',
                title="High-Risk Merchant Categories (Hybrid ML)",
                color='High-Risk Alerts',
                color_continuous_scale='reds'
            )
            st.plotly_chart(fig_cat, config={'displayModeBar': False, 'responsive': True})
        else:
            st.info("No high-risk merchant categories identified")

# Enhanced Reporting section
st.divider()
st.subheader("📈 Hybrid ML-Powered Reporting & Analytics")

col1, col2 = st.columns(2)

with col1:
    if st.button("Generate Hybrid ML Insights Report", width='stretch'):
        if fraud_alerts:
            report_data = {
                "report_generated": str(datetime.now()),
                "time_period_analyzed": "All available data",
                "total_alerts": len(fraud_alerts),
                "active_alerts": len(active_alerts),
                "high_priority_alerts": len(high_priority),
                "hybrid_ml_metrics": {
                    "average_fraud_probability": f"{fraud_patterns.get('avg_fraud_probability', 0):.2%}",
                    "high_risk_users": len(fraud_patterns.get('high_risk_users_ml', {})),
                    "trend_direction": fraud_patterns.get('hybrid_ml_insights', {}).get('trend_direction', 'unknown'),
                    "peak_fraud_hours": fraud_patterns.get('hybrid_ml_insights', {}).get('peak_hours', []),
                    "emerging_patterns": fraud_patterns.get('hybrid_ml_insights', {}).get('emerging_patterns', [])
                },
                "system_configuration": {
                    "models_active": "Sri Lanka + Original Hybrid",
                    "smart_routing": "Enabled",
                    "geographic_intelligence": "Active"
                },
                "data_quality": {
                    "alerts_analyzed": len(fraud_alerts),
                    "time_range_days": "N/A",
                    "data_completeness": "High" if len(fraud_alerts) >= 10 else "Medium"
                },
                "prevention_recommendations": hybrid_ml_insights.get('prevention_recommendations', [])
            }
            
            st.success("🤖 Hybrid ML Insights Report Generated!")
            st.json(report_data)
        else:
            st.info("No data available for hybrid ML report")

with col2:
    if st.button("Export Hybrid ML Analytics Data", width='stretch'):
        if fraud_alerts:
            export_data = []
            for alert in fraud_alerts:
                export_alert = {
                    'Alert ID': alert.get('alert_id'),
                    'Transaction ID': alert.get('transaction_id'),
                    'User ID': alert.get('user_id'),
                    'Amount': alert.get('amount'),
                    'Hybrid ML Fraud Probability': alert.get('fraud_probability'),
                    'Risk Level': alert.get('risk_level', 'MEDIUM_RISK'),
                    'Merchant': alert.get('merchant'),
                    'Priority': alert.get('priority'),
                    'Status': alert.get('status'),
                    'Timestamp': alert.get('timestamp'),
                    'Hybrid ML Risk Level': 'High' if alert.get('fraud_probability', 0) > 0.8 else 'Medium' if alert.get('fraud_probability', 0) > 0.6 else 'Low'
                }
                export_data.append(export_alert)
            
            df_export = pd.DataFrame(export_data)
            csv_data = df_export.to_csv(index=False)
            
            st.download_button(
                label="Download Hybrid ML Analytics CSV",
                data=csv_data,
                file_name=f"hybrid_ml_fraud_analytics_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                width='stretch'
            )

# Additional Hybrid ML Visualizations
if fraud_alerts and len(fraud_alerts) >= 5:
    st.subheader("🌍 Geographic Fraud Patterns (Hybrid ML)")
    
    heatmap_data = generate_risk_heatmap_data(fraud_alerts)
    if heatmap_data:
        heatmap_df = pd.DataFrame(heatmap_data)
        fig_map = px.density_mapbox(
            heatmap_df,
            lat='lat',
            lon='lon',
            z='risk',
            radius=20,
            center=dict(lat=40.7128, lon=-74.0060),
            zoom=3,
            mapbox_style="stamen-toner",
            title="Hybrid ML Fraud Risk Geographic Heatmap",
            color_continuous_scale="reds"
        )
        st.plotly_chart(fig_map, config={'displayModeBar': False, 'responsive': True})

# Footer with Hybrid ML status
st.divider()
hybrid_status = "Active (Sri Lanka + Original)" if hybrid_model_loaded else "Inactive"
data_status = f"Analyzing {len(fraud_alerts)} alerts" if fraud_alerts else "No alert data"
st.caption(f"Hybrid ML-Powered Fraud Alert System • Hybrid ML: {hybrid_status} • {data_status} • Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")