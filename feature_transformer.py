# feature_transformer.py - EXACT MATCH TO COLAB
import pandas as pd
import numpy as np
from datetime import datetime
import time

class FraudFeatureTransformer:
    def __init__(self):
        # High risk hours from your EDA
        self.high_risk_hours = [2, 3, 4, 22, 23, 0]
        
        # EXACT feature order from your model
        self.expected_features = [
            'cc_num', 'gender', 'lat', 'long', 'city_pop', 'unix_time', 
            'merch_lat', 'merch_long', 'hour', 'day_of_week', 'is_weekend', 
            'month', 'cat_entertainment', 'cat_food_dining', 'cat_gas_transport',
            'cat_grocery_net', 'cat_grocery_pos', 'cat_health_fitness', 
            'cat_home', 'cat_kids_pets', 'cat_misc_net', 'cat_misc_pos', 
            'cat_personal_care', 'cat_shopping_net', 'cat_shopping_pos', 
            'cat_travel', 'amt_scaled', 'high_risk_hour'
        ]
        
    def transform_transaction(self, transaction_data, user_data, merch_lat, merch_lon):
        """Transform transaction data to EXACTLY match Colab training features"""
        
        current_time = datetime.now()
        unix_time = int(time.mktime(current_time.timetuple()))
        
        # Get user location with defaults
        user_lat = user_data.get('lat', 40.7618)
        user_lon = user_data.get('lon', -73.9708)
        
        # Calculate geographic distance for debugging
        geo_distance = abs(user_lat - merch_lat) + abs(user_lon - merch_lon)
        
        print(f"🔧 FEATURE TRANSFORM DEBUG:")
        print(f"  User: ({user_lat:.4f}, {user_lon:.4f})")
        print(f"  Merchant: ({merch_lat:.4f}, {merch_lon:.4f})")
        print(f"  Geographic Distance: {geo_distance:.2f}°")
        print(f"  Amount: ${transaction_data['amount']:,.2f}")
        print(f"  Category: {transaction_data.get('category')}")
        print(f"  Hour: {current_time.hour}")
        
        # 1. Create features in EXACT order expected by model
        features = {
            'cc_num': int(str(transaction_data.get('card_number', '00000000'))[-8:]),
            'gender': 1 if user_data.get('gender', 'M') == 'M' else 0,
            'lat': float(user_lat), 
            'long': float(user_lon), 
            'city_pop': self.get_city_population(user_lat, user_lon),
            'unix_time': unix_time, 
            'merch_lat': float(merch_lat), 
            'merch_long': float(merch_lon),
            'hour': current_time.hour, 
            'day_of_week': current_time.weekday(),
            'is_weekend': 1 if current_time.weekday() >= 5 else 0,
            'month': current_time.month,
            # 🎯 CRITICAL FIX: Use same scaling as Colab
            'amt_scaled': float((transaction_data['amount'] - 70.0) / 200.0),
            'high_risk_hour': 1 if current_time.hour in self.high_risk_hours else 0
        }
        
        # 2. Category encoding (EXACT one-hot like Colab)
        category = transaction_data.get('category', 'misc_pos')
        all_categories = [
            'entertainment', 'food_dining', 'gas_transport', 'grocery_net', 'grocery_pos',
            'health_fitness', 'home', 'kids_pets', 'misc_net', 'misc_pos', 
            'personal_care', 'shopping_net', 'shopping_pos', 'travel'
        ]
        
        for cat in all_categories:
            features[f'cat_{cat}'] = 1 if category == cat else 0
        
        # 3. Create DataFrame with EXACT column order
        df = pd.DataFrame([features])
        
        # Ensure ALL expected features exist in EXACT order
        for col in self.expected_features:
            if col not in df.columns:
                df[col] = 0  # Add missing features with default value
        
        # Reorder to match model expectations exactly
        df = df[self.expected_features]
        
        print(f"✅ Transformed to {len(df.columns)} features")
        print(f"🔍 Key feature values:")
        print(f"  - amt_scaled: {df['amt_scaled'].values[0]:.4f}")
        print(f"  - high_risk_hour: {df['high_risk_hour'].values[0]}")
        print(f"  - lat: {df['lat'].values[0]:.4f}")
        print(f"  - merch_lat: {df['merch_lat'].values[0]:.4f}")
        
        # Show active category
        active_cats = [col for col in df.columns if col.startswith('cat_') and df[col].values[0] == 1]
        if active_cats:
            print(f"  - Active category: {active_cats[0]}")
        
        return df
    
    def get_city_population(self, lat, lon):
        """Estimate city population - consistent with training"""
        # Simple estimation based on coordinates
        if abs(lat - 40.7128) < 1 and abs(lon - (-74.0060)) < 1:  # NYC
            return 8419000
        elif abs(lat - 34.0522) < 1 and abs(lon - (-118.2437)) < 1:  # LA
            return 3980000
        elif abs(lat - 41.8781) < 1 and abs(lon - (-87.6298)) < 1:  # Chicago
            return 2716000
        else:
            return 500000  # Default medium city