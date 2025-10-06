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

def geocode_address(address):
    """Neutral geocoding without geographic bias"""
    try:
        base_url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address, 
            'format': 'json', 
            'limit': 1,
            'addressdetails': 1
        }
        headers = {'User-Agent': 'SecureBank-Fraud-Detection/1.0'}
        
        response = requests.get(base_url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
        
        # Fallback based on address content (neutral)
        address_lower = address.lower()
        
        # Sri Lanka indicators
        sri_lanka_indicators = ['sri lanka', 'colombo', 'galle', 'kandy', 'jaffna', 'negombo']
        if any(indicator in address_lower for indicator in sri_lanka_indicators):
            return 6.9271, 79.8612  # Colombo
        
        # US indicators
        us_indicators = ['new york', 'ny', 'california', 'ca', 'texas', 'tx', 'chicago', 'miami']
        if any(indicator in address_lower for indicator in us_indicators):
            return 40.7128, -74.0060  # New York
        
        # Default to international location (no bias)
        return 40.7128, -74.0060
        
    except Exception as e:
        print(f"Geocoding error: {e}")
        return 40.7128, -74.0060  # Default to international location

def is_in_sri_lanka(lat, lon):
    """Check if coordinates are in Sri Lanka"""
    sri_lanka_bounds = {
        'min_lat': 5.5, 'max_lat': 10.0,
        'min_lon': 79.0, 'max_lon': 82.0
    }
    
    return (sri_lanka_bounds['min_lat'] <= lat <= sri_lanka_bounds['max_lat'] and
            sri_lanka_bounds['min_lon'] <= lon <= sri_lanka_bounds['max_lon'])

def get_city_population(lat, lon):
    """Estimate city population based on coordinates"""
    try:
        if is_in_sri_lanka(lat, lon):
            # Sri Lanka cities
            if abs(lat - 6.9271) < 0.5 and abs(lon - 79.8612) < 0.5:
                return 600000  # Colombo
            elif abs(lat - 6.0535) < 0.5 and abs(lon - 80.2210) < 0.5:
                return 100000  # Galle
            elif abs(lat - 7.2906) < 0.5 and abs(lon - 80.6337) < 0.5:
                return 125000  # Kandy
            else:
                return 50000   # Other Sri Lanka areas
        else:
            # International cities
            if abs(lat - 40.7128) < 5 and abs(lon - (-74.0060)) < 5:
                return 8419000  # NYC
            elif abs(lat - 34.0522) < 5 and abs(lon - (-118.2437)) < 5:
                return 3980000  # LA
            elif abs(lat - 41.8781) < 5 and abs(lon - (-87.6298)) < 5:
                return 2716000  # Chicago
            else:
                return 500000   # Default medium city
    except:
        return 500000

def scale_amount(amount):
    """Scale amount for model input"""
    scaled = (amount - 70.0) / 200.0
    return float(scaled)

def add_pending_approval(transaction_data, fraud_probability, risk_level):
    """Add transaction to pending approvals for admin review"""
    try:
        with open('data/pending_approvals.json', 'r') as f:
            pending = json.load(f)
    except:
        pending = []
    
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
    """Update transaction status after admin review"""
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
    
    try:
        with open('data/transactions.json', 'r') as f:
            transactions = json.load(f)
    except:
        transactions = {}
    
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

def create_fraud_alert(transaction_data, fraud_probability, risk_level):
    """Create fraud alert"""
    try:
        with open('data/fraud_alerts.json', 'r') as f:
            alerts = json.load(f)
    except:
        alerts = []
    
    fraud_probability = convert_to_serializable(fraud_probability)
    transaction_data = convert_to_serializable(transaction_data)
    
    alert_data = {
        'alert_id': f"ALERT{int(time.time())}",
        'transaction_id': transaction_data.get('transaction_id'),
        'user_id': st.session_state.current_user,
        'fraud_probability': fraud_probability,
        'risk_level': risk_level,
        'amount': transaction_data['amount'],
        'merchant': transaction_data['merchant_name'],
        'timestamp': str(datetime.now()),
        'status': 'new',
        'priority': 'HIGH' if risk_level == 'HIGH_RISK' else 'MEDIUM'
    }
    
    alerts.append(alert_data)
    
    with open('data/fraud_alerts.json', 'w') as f:
        json.dump(alerts, f, indent=2, default=str)
    
    return alert_data['alert_id']

def ensure_data_directory():
    """Create data directory and files if they don't exist"""
    os.makedirs('data', exist_ok=True)
    
    files = ['users.json', 'transactions.json', 'pending_approvals.json', 'fraud_alerts.json']
    for file in files:
        file_path = f'data/{file}'
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                if file == 'users.json' or file == 'transactions.json':
                    json.dump({}, f)
                else:
                    json.dump([], f)