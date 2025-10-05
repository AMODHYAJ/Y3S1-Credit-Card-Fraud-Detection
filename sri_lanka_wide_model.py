# sri_lanka_wide_model.py - FIXED VERSION
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import joblib
import warnings
warnings.filterwarnings('ignore')

def create_sri_lanka_wide_dataset():
    """Create dataset covering all major Sri Lankan cities"""
    print("🔄 Creating Sri Lanka-wide transaction dataset...")
    
    n_samples = 10000  # Reduced for faster training
    np.random.seed(42)
    data = []
    
    # MAJOR SRI LANKAN CITIES WITH COORDINATES
    SRI_LANKA_CITIES = {
        'colombo': {'lat': 6.9271, 'lon': 79.8612, 'pop': 600000},
        'galle': {'lat': 6.0535, 'lon': 80.2210, 'pop': 100000},
        'kandy': {'lat': 7.2906, 'lon': 80.6337, 'pop': 125000},
        'jaffna': {'lat': 9.6615, 'lon': 80.0255, 'pop': 90000},
        'negombo': {'lat': 7.2086, 'lon': 79.8357, 'pop': 150000},
    }
    
    # =========================================================================
    # 🟢 LOW RISK PATTERNS ACROSS ALL CITIES
    # =========================================================================
    
    for city_name, city_info in SRI_LANKA_CITIES.items():
        city_lat, city_lon, city_pop = city_info['lat'], city_info['lon'], city_info['pop']
        
        # Local Grocery Shopping in each city (LOW RISK)
        for i in range(200):
            data.append(create_city_transaction(
                city_lat, city_lon, city_pop,
                amount_range=(5, 50),
                category='grocery_pos',
                hour_range=(8, 20),  # FIXED: Normal hours
                max_distance=0.02,
                is_fraud=0,
                description=f"Grocery in {city_name.title()}"
            ))
        
        # Local Food & Dining in each city (LOW RISK)
        for i in range(150):
            data.append(create_city_transaction(
                city_lat, city_lon, city_pop,
                amount_range=(10, 80),
                category='food_dining',
                hour_range=(11, 22),  # FIXED: Meal times
                max_distance=0.03,
                is_fraud=0,
                description=f"Dining in {city_name.title()}"
            ))
    
    # =========================================================================
    # 🔴 FRAUD PATTERNS ACROSS SRI LANKA
    # =========================================================================
    
    for city_name, city_info in SRI_LANKA_CITIES.items():
        city_lat, city_lon, city_pop = city_info['lat'], city_info['lon'], city_info['pop']
        
        # Local card testing fraud (HIGH RISK)
        for i in range(100):
            data.append(create_city_transaction(
                city_lat, city_lon, city_pop,
                amount_range=(1, 5),
                category='grocery_pos',
                hour_range=(2, 5),  # FIXED: Late night hours
                max_distance=0.02,
                is_fraud=1,
                description=f"Card testing fraud in {city_name.title()}"
            ))
        
        # High-value local fraud (HIGH RISK)
        for i in range(80):
            data.append(create_city_transaction(
                city_lat, city_lon, city_pop,
                amount_range=(300, 1000),
                category='shopping_pos',
                hour_range=(8, 12),  # FIXED: Business hours but high value
                max_distance=0.03,
                is_fraud=1,
                description=f"High-value fraud in {city_name.title()}"
            ))
    
    # =========================================================================
    # 🟡 MEDIUM RISK PATTERNS (ADDED FOR BALANCE)
    # =========================================================================
    
    for city_name, city_info in SRI_LANKA_CITIES.items():
        city_lat, city_lon, city_pop = city_info['lat'], city_info['lon'], city_info['pop']
        
        # Medium value transactions (MEDIUM RISK)
        for i in range(100):
            data.append(create_city_transaction(
                city_lat, city_lon, city_pop,
                amount_range=(100, 300),
                category='shopping_pos',
                hour_range=(10, 18),
                max_distance=0.04,
                is_fraud=0,
                description=f"Medium shopping in {city_name.title()}"
            ))
        
        # Late night legitimate transactions (MEDIUM RISK)
        for i in range(80):
            data.append(create_city_transaction(
                city_lat, city_lon, city_pop,
                amount_range=(20, 60),
                category='misc_pos',
                hour_range=(22, 24),  # FIXED: 10 PM to 12 AM
                max_distance=0.02,
                is_fraud=0,
                description=f"Late night in {city_name.title()}"
            ))
    
    # =========================================================================
    # INTERNATIONAL TRANSACTIONS FOR COMPARISON
    # =========================================================================
    
    # International Fraud (HIGH RISK)
    for i in range(300):
        data.append({
            'cc_num': np.random.randint(10000000, 99999999),
            'amt': np.random.uniform(500, 5000),
            'lat': 6.9271 + np.random.normal(0, 0.01),  # Sri Lankan user
            'long': 79.8612 + np.random.normal(0, 0.01),
            'merch_lat': 25.1997 + np.random.normal(0, 0.5),  # Dubai
            'merch_long': 55.2795 + np.random.normal(0, 0.5),
            'category': 'shopping_net',
            'hour': np.random.randint(0, 6),  # Unusual hours
            'city_pop': 600000,
            'is_fraud': 1
        })
    
    # International Legitimate (MEDIUM RISK)
    for i in range(200):
        data.append({
            'cc_num': np.random.randint(10000000, 99999999),
            'amt': np.random.uniform(100, 300),
            'lat': 6.9271 + np.random.normal(0, 0.01),  # Sri Lankan user
            'long': 79.8612 + np.random.normal(0, 0.01),
            'merch_lat': 34.0522 + np.random.normal(0, 0.1),  # California
            'merch_long': -118.2437 + np.random.normal(0, 0.1),
            'category': 'shopping_net',
            'hour': np.random.randint(10, 18),  # Normal hours
            'city_pop': 600000,
            'is_fraud': 0
        })
    
    df = pd.DataFrame(data)
    df = engineer_sri_lanka_features(df)
    
    print(f"✅ Sri Lanka-wide dataset created: {len(df)} transactions")
    print(f"   Cities covered: {len(SRI_LANKA_CITIES)}")
    print(f"   Low Risk Local: {len(df[(df['is_local_sri_lanka'] == 1) & (df['is_fraud'] == 0)])}")
    print(f"   High Risk Local Fraud: {len(df[(df['is_local_sri_lanka'] == 1) & (df['is_fraud'] == 1)])}")
    print(f"   Overall Fraud Rate: {df['is_fraud'].mean():.2%}")
    
    return df

def create_city_transaction(city_lat, city_lon, city_pop, amount_range, category, hour_range, max_distance, is_fraud, description):
    """Create transaction within a specific Sri Lankan city"""
    user_lat = city_lat + np.random.normal(0, 0.005)
    user_lon = city_lon + np.random.normal(0, 0.005)
    
    # Merchant within the same city
    merch_lat = user_lat + np.random.uniform(-max_distance, max_distance)
    merch_lon = user_lon + np.random.uniform(-max_distance, max_distance)
    
    # FIXED: Handle hour ranges properly
    if hour_range[0] < hour_range[1]:
        hour = np.random.randint(hour_range[0], hour_range[1])
    else:
        # For ranges like (22, 24) - handle midnight wrap-around
        hour = np.random.randint(hour_range[0], 24)
    
    return {
        'cc_num': np.random.randint(10000000, 99999999),
        'amt': np.random.uniform(amount_range[0], amount_range[1]),
        'lat': user_lat,
        'long': user_lon,
        'merch_lat': merch_lat,
        'merch_long': merch_lon,
        'category': category,
        'hour': hour,
        'city_pop': city_pop,
        'is_fraud': is_fraud,
        'description': description
    }

def engineer_sri_lanka_features(df):
    """Enhanced feature engineering for Sri Lanka context"""
    
    # Geographic features
    df['geo_distance'] = np.sqrt(
        (df['lat'] - df['merch_lat'])**2 + (df['long'] - df['merch_long'])**2
    )
    
    # Sri Lanka specific local indicators
    df['is_local_sri_lanka'] = (df['geo_distance'] < 0.1).astype(int)  # ~11km
    df['is_same_city'] = (df['geo_distance'] < 0.05).astype(int)  # ~5.5km
    df['is_very_local'] = (df['geo_distance'] < 0.02).astype(int)  # ~2.2km
    
    # Sri Lanka population context
    df['is_metro'] = (df['city_pop'] > 500000).astype(int)  # Colombo
    df['is_large_city'] = ((df['city_pop'] >= 100000) & (df['city_pop'] <= 500000)).astype(int)  # Galle, Kandy
    df['is_small_city'] = (df['city_pop'] < 100000).astype(int)  # Other cities
    
    # Amount features adjusted for Sri Lanka context
    df['amt_scaled'] = (df['amt'] - 70.0) / 200.0
    df['is_small_amount_lkr'] = (df['amt'] < 30).astype(int)  # < 30 USD ~ 10,000 LKR
    df['is_medium_amount_lkr'] = ((df['amt'] >= 30) & (df['amt'] < 100)).astype(int)  # 30-100 USD
    df['is_large_amount_lkr'] = (df['amt'] >= 100).astype(int)  # > 100 USD ~ 33,000 LKR
    
    # Time features considering Sri Lanka timezone (UTC+5:30)
    df['high_risk_hour'] = df['hour'].apply(lambda x: 1 if x in [2, 3, 4, 22, 23, 0] else 0)
    df['business_hours_lk'] = df['hour'].apply(lambda x: 1 if 8 <= x <= 20 else 0)  # Longer business hours
    df['late_night_lk'] = df['hour'].apply(lambda x: 1 if 0 <= x <= 5 else 0)
    
    # Sri Lanka specific behavioral patterns
    df['amount_to_distance_ratio'] = df['amt'] / (df['geo_distance'] + 0.001)
    
    # Category encoding
    categories = ['entertainment', 'food_dining', 'gas_transport', 'grocery_net', 'grocery_pos',
                 'health_fitness', 'home', 'kids_pets', 'misc_net', 'misc_pos', 
                 'personal_care', 'shopping_net', 'shopping_pos', 'travel']
    
    for cat in categories:
        df[f'cat_{cat}'] = (df['category'] == cat).astype(int)
    
    # Additional features
    df['gender'] = np.random.choice([0, 1], len(df))
    df['unix_time'] = np.random.randint(1609459200, 1640995200, len(df))
    df['day_of_week'] = np.random.randint(0, 7, len(df))
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['month'] = np.random.randint(1, 13, len(df))
    
    return df

def train_sri_lanka_wide_model():
    """Train model for entire Sri Lanka"""
    print("🎯 Training Sri Lanka-wide fraud detection model...")
    
    df = create_sri_lanka_wide_dataset()
    
    # Feature columns including Sri Lanka specific features
    feature_columns = [
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
    
    # Ensure all columns exist
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0
    
    X = df[feature_columns]
    y = df['is_fraud']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    
    print(f"📊 Training set: {X_train.shape}")
    print(f"🎯 Fraud rate: {y_train.mean():.3%}")
    
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=len(y_train[y_train==0]) / len(y_train[y_train==1]),
        random_state=42,
        eval_metric='auc'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc_score = roc_auc_score(y_test, y_pred_proba)
    
    print(f"✅ Sri Lanka-wide model trained!")
    print(f"📊 AUC Score: {auc_score:.4f}")
    
    # Test key scenarios
    test_sri_lanka_scenarios(model, feature_columns)
    
    return model, feature_columns

def test_sri_lanka_scenarios(model, feature_columns):
    """Test key Sri Lanka scenarios"""
    print("\n🧪 Testing Sri Lanka Scenarios...")
    
    test_cases = [
        # 🟢 GALLE - LOW RISK
        {
            'name': 'Galle Cargills',
            'amount': 15.0,
            'category': 'grocery_pos',
            'user_lat': 6.0535, 'user_lon': 80.2210,
            'merch_lat': 6.0540, 'merch_lon': 80.2200,
            'hour': 14,
            'expected': 'LOW'
        },
        # 🟢 COLOMBO - LOW RISK  
        {
            'name': 'Colombo Restaurant',
            'amount': 35.0,
            'category': 'food_dining',
            'user_lat': 6.9271, 'user_lon': 79.8612,
            'merch_lat': 6.9280, 'merch_lon': 79.8620,
            'hour': 19,
            'expected': 'LOW'
        },
        # 🔴 INTERNATIONAL - HIGH RISK
        {
            'name': 'Dubai Luxury',
            'amount': 2500.0,
            'category': 'shopping_net',
            'user_lat': 6.9271, 'user_lon': 79.8612, 
            'merch_lat': 25.1997, 'merch_lon': 55.2795,
            'hour': 3,
            'expected': 'HIGH'
        },
        # 🟡 MEDIUM RISK
        {
            'name': 'Colombo High Value',
            'amount': 450.0,
            'category': 'shopping_pos',
            'user_lat': 6.9271, 'user_lon': 79.8612,
            'merch_lat': 6.9300, 'merch_lon': 79.8600,
            'hour': 15,
            'expected': 'MEDIUM'
        }
    ]
    
    for test in test_cases:
        features = create_test_features(test, feature_columns)
        fraud_prob = model.predict_proba(features)[0][1]
        
        if fraud_prob < 0.1:
            risk = 'LOW'
        elif fraud_prob < 0.3:
            risk = 'MEDIUM'
        else:
            risk = 'HIGH'
            
        status = '✅' if risk == test['expected'] else '❌'
        
        print(f"{status} {test['name']}: {fraud_prob:.2%} → {risk} (expected: {test['expected']})")

def create_test_features(test_case, feature_columns):
    """Create features for testing"""
    geo_distance = np.sqrt(
        (test_case['user_lat'] - test_case['merch_lat'])**2 + 
        (test_case['user_lon'] - test_case['merch_lon'])**2
    )
    
    # Estimate city population
    if test_case['user_lat'] == 6.0535:  # Galle
        city_pop = 100000
    else:  # Colombo or other
        city_pop = 600000
    
    features = {
        'cc_num': 12345678, 'gender': 0,
        'lat': test_case['user_lat'], 'long': test_case['user_lon'], 
        'city_pop': city_pop, 'unix_time': 1759572359,
        'merch_lat': test_case['merch_lat'], 'merch_long': test_case['merch_lon'],
        'hour': test_case['hour'], 'day_of_week': 2, 'is_weekend': 0, 'month': 10,
        'amt_scaled': (test_case['amount'] - 70.0) / 200.0,
        'high_risk_hour': 1 if test_case['hour'] in [2,3,4,22,23,0] else 0,
        'geo_distance': geo_distance,
        'is_local_sri_lanka': 1 if geo_distance < 0.1 else 0,
        'is_same_city': 1 if geo_distance < 0.05 else 0,
        'is_very_local': 1 if geo_distance < 0.02 else 0,
        'is_metro': 1 if city_pop > 500000 else 0,
        'is_large_city': 1 if 100000 <= city_pop <= 500000 else 0,
        'is_small_city': 1 if city_pop < 100000 else 0,
        'is_small_amount_lkr': 1 if test_case['amount'] < 30 else 0,
        'is_medium_amount_lkr': 1 if 30 <= test_case['amount'] < 100 else 0,
        'is_large_amount_lkr': 1 if test_case['amount'] >= 100 else 0,
        'business_hours_lk': 1 if 8 <= test_case['hour'] <= 20 else 0,
        'late_night_lk': 1 if 0 <= test_case['hour'] <= 5 else 0,
        'amount_to_distance_ratio': test_case['amount'] / (geo_distance + 0.001)
    }
    
    # Category encoding
    all_categories = ['entertainment', 'food_dining', 'gas_transport', 'grocery_net', 'grocery_pos',
                     'health_fitness', 'home', 'kids_pets', 'misc_net', 'misc_pos', 
                     'personal_care', 'shopping_net', 'shopping_pos', 'travel']
    
    for cat in all_categories:
        features[f'cat_{cat}'] = 1 if test_case['category'] == cat else 0
    
    # Create DataFrame
    df = pd.DataFrame([features])
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0
    
    return df[feature_columns]

def main():
    """Main function to train and save Sri Lanka model"""
    print("🚀 SRI LANKA FRAUD DETECTION MODEL TRAINING")
    print("=" * 50)
    
    # Create models directory
    import os
    os.makedirs('models', exist_ok=True)
    
    # Train model
    model, feature_columns = train_sri_lanka_wide_model()
    
    # Save model
    model_data = {
        'model': model,
        'feature_columns': feature_columns,
        'model_type': 'sri_lanka_optimized',
        'timestamp': pd.Timestamp.now()
    }
    
    joblib.dump(model_data, 'models/sri_lanka_wide_model.joblib')
    print(f"\n💾 Model saved: models/sri_lanka_wide_model.joblib")
    print("🎯 Sri Lanka model ready for integration!")

if __name__ == "__main__":
    main()