# sri_lanka_integration.py
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import time

class SriLankaFeatureTransformer:
    def __init__(self):
        # Sri Lanka specific settings
        self.high_risk_hours = [2, 3, 4, 22, 23, 0]
        
        # Sri Lanka model expects these features
        self.expected_features = [
            'cc_num', 'gender', 'lat', 'long', 'city_pop', 'unix_time', 
            'merch_lat', 'merch_long', 'hour', 'day_of_week', 'is_weekend', 
            'month', 'cat_entertainment', 'cat_food_dining', 'cat_gas_transport',
            'cat_grocery_net', 'cat_grocery_pos', 'cat_health_fitness', 
            'cat_home', 'cat_kids_pets', 'cat_misc_net', 'cat_misc_pos', 
            'cat_personal_care', 'cat_shopping_net', 'cat_shopping_pos', 
            'cat_travel', 'amt_scaled', 'high_risk_hour', 'geo_distance', 
            'is_local_sri_lanka', 'is_same_city', 'is_very_local', 
            'is_metro', 'is_large_city', 'is_small_city',
            'is_small_amount_lkr', 'is_medium_amount_lkr', 'is_large_amount_lkr',
            'business_hours_lk', 'late_night_lk', 'amount_to_distance_ratio'
        ]
    
    def transform_transaction(self, transaction_data, user_data, merch_lat, merch_lon):
        """Transform transaction for Sri Lanka model"""
        current_time = datetime.now()
        unix_time = int(time.mktime(current_time.timetuple()))
        
        # Get user location with Sri Lanka defaults
        user_lat = user_data.get('lat', 6.9271)  # Default to Colombo
        user_lon = user_data.get('lon', 79.8612)
        
        # Calculate geographic metrics
        geo_distance = np.sqrt((user_lat - merch_lat)**2 + (user_lon - merch_lon)**2)
        
        # Sri Lanka specific features
        city_pop = self.get_sri_lanka_population(user_lat, user_lon)
        is_local = 1 if geo_distance < 0.1 else 0
        is_same_city = 1 if geo_distance < 0.05 else 0
        is_very_local = 1 if geo_distance < 0.02 else 0
        
        # City size classification for Sri Lanka
        is_metro = 1 if city_pop > 500000 else 0  # Colombo
        is_large_city = 1 if 100000 <= city_pop <= 500000 else 0  # Galle, Kandy
        is_small_city = 1 if city_pop < 100000 else 0
        
        # Amount classification for Sri Lanka context
        amount = transaction_data['amount']
        is_small_amount = 1 if amount < 30 else 0      # < 30 USD ~ 10,000 LKR
        is_medium_amount = 1 if 30 <= amount < 100 else 0  # 30-100 USD
        is_large_amount = 1 if amount >= 100 else 0    # > 100 USD ~ 33,000 LKR
        
        features = {
            'cc_num': int(str(transaction_data.get('card_number', '00000000'))[-8:]),
            'gender': 1 if user_data.get('gender', 'M') == 'M' else 0,
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
            'amt_scaled': float((amount - 70.0) / 200.0),
            'high_risk_hour': 1 if current_time.hour in self.high_risk_hours else 0,
            'geo_distance': float(geo_distance),
            'is_local_sri_lanka': is_local,
            'is_same_city': is_same_city,
            'is_very_local': is_very_local,
            'is_metro': is_metro,
            'is_large_city': is_large_city,
            'is_small_city': is_small_city,
            'is_small_amount_lkr': is_small_amount,
            'is_medium_amount_lkr': is_medium_amount,
            'is_large_amount_lkr': is_large_amount,
            'business_hours_lk': 1 if 8 <= current_time.hour <= 20 else 0,
            'late_night_lk': 1 if 0 <= current_time.hour <= 5 else 0,
            'amount_to_distance_ratio': amount / (geo_distance + 0.001)
        }
        
        # Category encoding
        category = transaction_data.get('category', 'misc_pos')
        all_categories = [
            'entertainment', 'food_dining', 'gas_transport', 'grocery_net', 'grocery_pos',
            'health_fitness', 'home', 'kids_pets', 'misc_net', 'misc_pos', 
            'personal_care', 'shopping_net', 'shopping_pos', 'travel'
        ]
        
        for cat in all_categories:
            features[f'cat_{cat}'] = 1 if category == cat else 0
        
        # Create DataFrame
        df = pd.DataFrame([features])
        
        # Ensure all expected features exist
        for col in self.expected_features:
            if col not in df.columns:
                df[col] = 0
        
        df = df[self.expected_features]
        
        print(f"🇱🇰 Sri Lanka Model: Transformed {len(df.columns)} features")
        print(f"   Location: ({user_lat:.4f}, {user_lon:.4f}) → ({merch_lat:.4f}, {merch_lon:.4f})")
        print(f"   Distance: {geo_distance:.4f}° | Local: {is_local} | Amount: ${amount}")
        
        return df
    
    def get_sri_lanka_population(self, lat, lon):
        """Get population for Sri Lankan cities"""
        # Major Sri Lankan cities
        cities = {
            (6.9271, 79.8612): 600000,   # Colombo
            (6.0535, 80.2210): 100000,   # Galle
            (7.2906, 80.6337): 125000,   # Kandy
            (9.6615, 80.0255): 90000,    # Jaffna
            (7.2086, 79.8357): 150000,   # Negombo
            (5.9480, 80.5353): 80000,    # Matara
        }
        
        for city_coords, pop in cities.items():
            city_lat, city_lon = city_coords
            distance = np.sqrt((lat - city_lat)**2 + (lon - city_lon)**2)
            if distance < 0.1:  # Within city radius
                return pop
        
        return 50000  # Default for other areas

def load_sri_lanka_model():
    """Load the Sri Lanka optimized model"""
    try:
        model_data = joblib.load('models/sri_lanka_wide_model.joblib')
        print("✅ Sri Lanka wide model loaded!")
        return model_data['model'], model_data['feature_columns']
    except Exception as e:
        print(f"❌ Sri Lanka model not found: {e}")
        return None, None