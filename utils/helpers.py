# utils/helpers.py
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

def scale_amount(amount):
    return float((amount - 70.0) / 200.0)  # Ensure native float

def get_city_population(lat, lon):
    if abs(lat - 40.7128) < 1 and abs(lon - (-74.0060)) < 1:
        return 8419000
    elif abs(lat - 34.0522) < 1 and abs(lon - (-118.2437)) < 1:
        return 3980000
    else:
        return 500000

def preprocess_transaction(transaction_data, user_lat, user_lon, merch_lat, merch_lon):
    current_time = datetime.now()
    unix_time = int(time.mktime(current_time.timetuple()))
    city_pop = get_city_population(user_lat, user_lon)
    
    input_data = {
        'cc_num': int(str(transaction_data['card_number'])[-8:]),
        'gender': 1 if transaction_data['gender'] == 'M' else 0,
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
        input_data[f'cat_{cat}'] = 1 if transaction_data['category'] == cat else 0
    
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
        json.dump(pending, f, indent=2, default=str)  # Added default=str for safety
    
    return approval_data['transaction_id']

def update_transaction_status(transaction_id, status, admin_notes=None):
    """Update transaction status after admin review"""
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
    
    # Add to transaction history
    try:
        with open('data/transactions.json', 'r') as f:
            transactions = json.load(f)
    except:
        transactions = {}
    
    user = st.session_state.current_user
    if user not in transactions:
        transactions[user] = []
    
    # Find and update the transaction
    for tx in transactions[user]:
        if tx.get('transaction_id') == transaction_id:
            tx['status'] = status
            tx['admin_review'] = admin_notes
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

def ensure_data_directory():
    """Create data directory and files if they don't exist"""
    os.makedirs('data', exist_ok=True)
    
    # Create empty JSON files if they don't exist
    files = ['users.json', 'transactions.json', 'pending_approvals.json', 'fraud_alerts.json']
    for file in files:
        file_path = f'data/{file}'
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f)