import pandas as pd
import numpy as np
import requests
import json
import os
from datetime import datetime
import time
import streamlit as st

def convert_to_serializable(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj

# Geocoding function
def geocode_address(address):
    try:
        base_url = "https://nominatim.openstreetmap.org/search"
        params = {'q': address, 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'SecureBank-Fraud-Detection/1.0'}
        
        response = requests.get(base_url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
        return 40.7128, -74.0060  # Default NYC coordinates
    except:
        return 40.7128, -74.0060

def get_city_population(lat, lon):
    """Estimate city population based on coordinates - more dynamic"""
    # This would ideally use a real geospatial database
    # For demo purposes, using a simple calculation based on density
    try:
        # Simple population estimation based on typical urban densities
        if abs(lat - 40.7128) < 5 and abs(lon - (-74.0060)) < 5:  # New York area
            return 8419000
        elif abs(lat - 34.0522) < 5 and abs(lon - (-118.2437)) < 5:  # LA area
            return 3980000
        elif abs(lat - 41.8781) < 5 and abs(lon - (-87.6298)) < 5:  # Chicago area
            return 2716000
        else:
            # Estimate based on typical city sizes
            return max(50000, int(1000000 * (1 - (abs(lat) / 90))))  # Rough estimate
    except:
        return 500000  # Default medium city

def scale_amount(amount):
    """Dynamic scaling based on typical transaction amounts"""
    # Use statistics from actual transaction data if available
    mean_amount = 70.0  # Could be calculated from real data
    std_amount = 200.0  # Could be calculated from real data
    return float((amount - mean_amount) / std_amount)

def preprocess_transaction(transaction_data, user_lat, user_lon, merch_lat, merch_lon):
    current_time = datetime.now()
    unix_time = int(time.mktime(current_time.timetuple()))
    city_pop = get_city_population(user_lat, user_lon)
    
    input_data = {
        'cc_num': int(str(transaction_data.get('card_number', '00000000'))[-8:]),
        'gender': 1 if transaction_data.get('gender', 'M') == 'M' else 0,
        'lat': float(user_lat), 
        'long': float(user_lon), 
        'city_pop': city_pop,
        'unix_time': unix_time, 
        'merch_lat': float(merch_lat), 
        'merch_long': float(merch_lon),
        'hour': current_time.hour, 
        'day_of_week': current_time.weekday(),
        'is_weekend': 1 if current_time.weekday() >= 5 else 0,
        'month': current_time.month, 
        'amt_scaled': float(scale_amount(transaction_data['amount'])),
        'high_risk_hour': 1 if current_time.hour in [2, 3, 4, 22, 23, 0] else 0
    }
    
    all_categories = ['entertainment', 'food_dining', 'gas_transport', 'grocery_net', 'grocery_pos',
                     'health_fitness', 'home', 'kids_pets', 'misc_net', 'misc_pos', 
                     'personal_care', 'shopping_net', 'shopping_pos', 'travel']
    
    for cat in all_categories:
        input_data[f'cat_{cat}'] = 1 if transaction_data.get('category') == cat else 0
    
    expected_columns = [
        'cc_num', 'gender', 'lat', 'long', 'city_pop', 'unix_time', 'merch_lat', 'merch_long',
        'hour', 'day_of_week', 'is_weekend', 'month', 'cat_entertainment', 'cat_food_dining',
        'cat_gas_transport', 'cat_grocery_net', 'cat_grocery_pos', 'cat_health_fitness',
        'cat_home', 'cat_kids_pets', 'cat_misc_net', 'cat_misc_pos', 'cat_personal_care',
        'cat_shopping_net', 'cat_shopping_pos', 'cat_travel', 'amt_scaled', 'high_risk_hour'
    ]
    
    df = pd.DataFrame([input_data])
    for col in expected_columns:
        if col not in df.columns:
            df[col] = 0
    
    return df[expected_columns]

def add_pending_approval(transaction_data, fraud_probability, risk_level):
    """Add transaction to pending approvals for admin review"""
    try:
        with open('data/pending_approvals.json', 'r') as f:
            pending = json.load(f)
    except:
        pending = []
    
    # Convert numpy types to native Python types
    fraud_probability = convert_to_serializable(fraud_probability)
    transaction_data = convert_to_serializable(transaction_data)
    
    approval_data = {
        'transaction_id': f"TX{int(time.time())}",
        'user_id': st.session_state.current_user,
        'transaction_data': transaction_data,
        'fraud_probability': fraud_probability,
        'risk_level': risk_level,
        'timestamp': str(datetime.now()),
        'status': 'pending',
        'admin_action': None
    }
    
    pending.append(approval_data)
    
    with open('data/pending_approvals.json', 'w') as f:
        json.dump(pending, f, indent=2, default=str)
    
    return approval_data['transaction_id']

def update_transaction_status(transaction_id, status, admin_notes=None):
    """Update transaction status after admin review - FIXED VERSION"""
    # Update pending approvals
    try:
        with open('data/pending_approvals.json', 'r') as f:
            pending = json.load(f)
    except:
        pending = []
    
    for tx in pending:
        if tx['transaction_id'] == transaction_id:
            tx['status'] = status
            tx['admin_action'] = admin_notes
            tx['resolved_at'] = str(datetime.now())
            break
    
    with open('data/pending_approvals.json', 'w') as f:
        json.dump(pending, f, indent=2, default=str)
    
    # Update transaction history
    try:
        with open('data/transactions.json', 'r') as f:
            transactions = json.load(f)
    except:
        transactions = {}
    
    # Find the user who owns this transaction
    user_id = None
    for user, user_txs in transactions.items():
        for tx in user_txs:
            if tx.get('transaction_id') == transaction_id:
                user_id = user
                tx['status'] = status
                tx['admin_review'] = admin_notes
                break
        if user_id:
            break
    
    with open('data/transactions.json', 'w') as f:
        json.dump(transactions, f, indent=2, default=str)

def create_fraud_alert(transaction_data, fraud_probability):
    """Create high-priority fraud alert for law enforcement"""
    try:
        with open('data/fraud_alerts.json', 'r') as f:
            alerts = json.load(f)
    except:
        alerts = []
    
    # Convert numpy types to native Python types
    fraud_probability = convert_to_serializable(fraud_probability)
    transaction_data = convert_to_serializable(transaction_data)
    
    alert_data = {
        'alert_id': f"ALERT{int(time.time())}",
        'transaction_id': transaction_data.get('transaction_id'),
        'user_id': st.session_state.current_user,
        'fraud_probability': fraud_probability,
        'amount': transaction_data['amount'],
        'merchant': transaction_data['merchant_name'],
        'timestamp': str(datetime.now()),
        'status': 'new',
        'priority': 'HIGH' if fraud_probability > 0.8 else 'MEDIUM'
    }
    
    alerts.append(alert_data)
    
    with open('data/fraud_alerts.json', 'w') as f:
        json.dump(alerts, f, indent=2, default=str)
    
    return alert_data['alert_id']

def send_real_time_alert(transaction_data, fraud_probability, risk_level):
    """Send real-time alerts for high-risk transactions"""
    alert_message = f"""
    🚨 FRAUD ALERT - IMMEDIATE ATTENTION REQUIRED
    
    Transaction ID: {transaction_data.get('transaction_id')}
    Amount: ${transaction_data['amount']:,.2f}
    Merchant: {transaction_data['merchant_name']}
    Fraud Probability: {fraud_probability:.2%}
    Risk Level: {risk_level}
    Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Recommended Action: {'IMMEDIATE BLOCK' if risk_level == 'HIGH_RISK' else 'Review Required'}
    """
    
    # In production, this would integrate with:
    # - Email systems
    # - SMS gateways  
    # - Slack/Teams webhooks
    # - Security incident management systems
    
    print(alert_message)  # For demo purposes
    return alert_message

def generate_fraud_report(timeframe='weekly'):
    """Generate comprehensive fraud detection report"""
    try:
        with open('data/fraud_alerts.json', 'r') as f:
            alerts = json.load(f)
        with open('data/transactions.json', 'r') as f:
            transactions = json.load(f)
        
        total_transactions = sum(len(user_txs) for user_txs in transactions.values())
        total_alerts = len(alerts)
        resolved_alerts = len([a for a in alerts if a['status'] == 'resolved'])
        
        report = {
            'report_date': str(datetime.now()),
            'timeframe': timeframe,
            'total_transactions': total_transactions,
            'fraud_alerts_generated': total_alerts,
            'alerts_resolved': resolved_alerts,
            'resolution_rate': (resolved_alerts / total_alerts * 100) if total_alerts > 0 else 0,
            'estimated_fraud_prevented': sum(a['amount'] for a in alerts if a['status'] == 'resolved'),
            'avg_fraud_probability': sum(a['fraud_probability'] for a in alerts) / total_alerts if total_alerts > 0 else 0
        }
        
        return report
    except Exception as e:
        return {'error': str(e)}

def ensure_data_directory():
    """Create data directory and files if they don't exist"""
    os.makedirs('data', exist_ok=True)
    
    # Create empty JSON files if they don't exist
    files = ['users.json', 'transactions.json', 'pending_approvals.json', 'fraud_alerts.json']
    for file in files:
        file_path = f'data/{file}'
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                if file == 'users.json' or file == 'transactions.json':
                    json.dump({}, f)
                else:
                    json.dump([], f)

def calculate_business_impact(fraud_alerts, transactions):
    """Calculate the business impact of fraud detection system"""
    try:
        total_transactions = sum(len(user_txs) for user_txs in transactions.values())
        blocked_fraud = len([alert for alert in fraud_alerts if alert.get('status') == 'resolved'])
        
        # Financial calculations
        avg_fraud_amount = 250  # Average fraud amount
        cost_per_investigation = 15  # Cost to investigate each alert
        recovery_rate = 0.3  # 30% recovery rate
        
        estimated_savings = blocked_fraud * avg_fraud_amount * recovery_rate
        investigation_costs = len(fraud_alerts) * cost_per_investigation
        net_savings = estimated_savings - investigation_costs
        
        return {
            'total_transactions': total_transactions,
            'blocked_fraud_cases': blocked_fraud,
            'fraud_prevention_rate': (blocked_fraud / total_transactions * 100) if total_transactions > 0 else 0,
            'estimated_savings': estimated_savings,
            'investigation_costs': investigation_costs,
            'net_savings': net_savings,
            'roi': (net_savings / investigation_costs) if investigation_costs > 0 else float('inf')
        }
    except Exception as e:
        return {'error': str(e)}