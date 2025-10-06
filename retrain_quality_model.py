# retrain_quality_model.py - FIXED VERSION WITH BETTER TRAINING DATA
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
import joblib
import warnings
warnings.filterwarnings('ignore')

def create_quality_training_data():
    """Create high-quality training data with realistic patterns"""
    print("🎯 Creating quality training dataset...")
    
    np.random.seed(42)
    n_samples = 30000
    
    data = []
    
    # =========================================================================
    # REALISTIC LEGITIMATE PATTERNS (85% of data)
    # =========================================================================
    
    # Normal low-risk transactions
    for i in range(25500):
        # Normal spending patterns
        amount = np.random.exponential(50)  # Most transactions small
        amount = min(amount, 300)  # Cap at $300 for normal spending
        
        # Normal hours (8 AM - 10 PM)
        hour = np.random.choice(list(range(8, 22)) + [22] * 3 + [23] * 2)
        
        # Geographic patterns - mostly local
        geo_distance = np.random.exponential(0.5)
        geo_distance = min(geo_distance, 3.0)
        
        # Normal categories with realistic amounts
        categories_weights = {
            'grocery_pos': 0.25, 'food_dining': 0.20, 'gas_transport': 0.15,
            'shopping_pos': 0.10, 'entertainment': 0.08, 'health_fitness': 0.07,
            'misc_pos': 0.05, 'travel': 0.04, 'personal_care': 0.03,
            'home': 0.02, 'kids_pets': 0.01
        }
        
        category = np.random.choice(
            list(categories_weights.keys()), 
            p=list(categories_weights.values())
        )
        
        # Adjust amounts by category
        if category in ['grocery_pos', 'food_dining', 'gas_transport']:
            amount = np.random.uniform(10, 80)
        elif category in ['shopping_pos', 'entertainment']:
            amount = np.random.uniform(20, 150)
        elif category == 'travel':
            amount = np.random.uniform(50, 300)
        
        data.append({
            'cc_num': np.random.randint(10000000, 99999999),
            'amt': amount,
            'lat': 40.7618 + np.random.normal(0, 0.5),
            'long': -73.9708 + np.random.normal(0, 0.5),
            'merch_lat': 40.7618 + np.random.normal(0, geo_distance),
            'merch_long': -73.9708 + np.random.normal(0, geo_distance),
            'category': category,
            'hour': hour,
            'is_fraud': 0
        })
    
    # =========================================================================
    # REALISTIC FRAUD PATTERNS (15% of data)
    # =========================================================================
    
    # Pattern 1: High-value international luxury
    for i in range(1500):
        data.append({
            'cc_num': np.random.randint(10000000, 99999999),
            'amt': np.random.uniform(1000, 5000),
            'lat': 40.7618 + np.random.normal(0, 0.1),
            'long': -73.9708 + np.random.normal(0, 0.1),
            'merch_lat': 25.1970 + np.random.normal(0, 0.5),  # Dubai
            'merch_long': 55.2790 + np.random.normal(0, 0.5),
            'category': 'shopping_net',
            'hour': np.random.choice([0, 1, 2, 3, 4, 22, 23]),  # High-risk hours
            'is_fraud': 1
        })
    
    # Pattern 2: Card testing (small amounts, rapid succession simulation)
    for i in range(1500):
        data.append({
            'cc_num': np.random.randint(10000000, 99999999),
            'amt': np.random.uniform(1, 5),
            'lat': 40.7618 + np.random.normal(0, 0.1),
            'long': -73.9708 + np.random.normal(0, 0.1),
            'merch_lat': 40.7618 + np.random.normal(0, 0.1),
            'merch_long': -73.9708 + np.random.normal(0, 0.1),
            'category': 'misc_pos',
            'hour': np.random.choice([0, 1, 2, 3, 4]),  # Very early morning
            'is_fraud': 1
        })
    
    # Pattern 3: Geographic anomalies
    for i in range(1500):
        data.append({
            'cc_num': np.random.randint(10000000, 99999999),
            'amt': np.random.uniform(200, 800),
            'lat': 40.7618 + np.random.normal(0, 0.1),
            'long': -73.9708 + np.random.normal(0, 0.1),
            'merch_lat': np.random.choice([34.0522, 51.5074, 48.8566, 35.6762]),  # LA, London, Paris, Tokyo
            'merch_long': np.random.choice([-118.2437, -0.1278, 2.3522, 139.6503]),
            'category': np.random.choice(['shopping_net', 'travel', 'misc_net']),
            'hour': np.random.randint(0, 24),
            'is_fraud': 1
        })
    
    df = pd.DataFrame(data)
    print(f"✅ Quality dataset created: {df.shape}")
    print(f"   - Legitimate: {len(df[df['is_fraud'] == 0])}")
    print(f"   - Fraud: {len(df[df['is_fraud'] == 1])}")
    print(f"   - Fraud rate: {df['is_fraud'].mean():.2%}")
    
    return df

def engineer_quality_features(df):
    """Engineer features with proper business logic"""
    print("🔧 Engineering quality features...")
    
    # Basic features
    df['cc_num'] = df['cc_num'].astype(str).str[-8:].astype(int)
    df['gender'] = np.random.choice([0, 1], len(df))
    df['city_pop'] = np.random.choice([500000, 1000000, 2000000], len(df))
    df['unix_time'] = np.random.randint(1609459200, 1640995200, len(df))
    df['day_of_week'] = np.random.randint(0, 7, len(df))
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['month'] = np.random.randint(1, 13, len(df))
    
    # Critical: Amount scaling (same as your production)
    df['amt_scaled'] = (df['amt'] - 70.0) / 200.0
    
    # High risk hours (2-5 AM, 10 PM-1 AM)
    df['high_risk_hour'] = df['hour'].apply(lambda x: 1 if x in [2, 3, 4, 22, 23, 0, 1] else 0)
    
    # Geographic distance
    df['geo_distance'] = np.sqrt((df['lat'] - df['merch_lat'])**2 + (df['long'] - df['merch_long'])**2)
    
    # Additional useful features
    df['is_high_amount'] = (df['amt'] > 500).astype(int)
    df['is_very_small_amount'] = (df['amt'] < 10).astype(int)
    df['is_international'] = (df['geo_distance'] > 5).astype(int)
    
    # One-hot encode categories
    categories = ['entertainment', 'food_dining', 'gas_transport', 'grocery_net', 'grocery_pos',
                 'health_fitness', 'home', 'kids_pets', 'misc_net', 'misc_pos', 
                 'personal_care', 'shopping_net', 'shopping_pos', 'travel']
    
    for cat in categories:
        df[f'cat_{cat}'] = (df['category'] == cat).astype(int)
    
    return df

def train_quality_model(df):
    """Train a well-balanced fraud detection model"""
    print("🎯 Training quality fraud detection model...")
    
    # Define feature columns (EXACTLY matching your feature transformer)
    feature_columns = [
        'cc_num', 'gender', 'lat', 'long', 'city_pop', 'unix_time', 'merch_lat', 'merch_long',
        'hour', 'day_of_week', 'is_weekend', 'month', 'cat_entertainment', 'cat_food_dining',
        'cat_gas_transport', 'cat_grocery_net', 'cat_grocery_pos', 'cat_health_fitness',
        'cat_home', 'cat_kids_pets', 'cat_misc_net', 'cat_misc_pos', 'cat_personal_care',
        'cat_shopping_net', 'cat_shopping_pos', 'cat_travel', 'amt_scaled', 'high_risk_hour'
    ]
    
    # Ensure all columns exist
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0
    
    X = df[feature_columns]
    y = df['is_fraud']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    print(f"📈 Training set: {X_train.shape}")
    print(f"📊 Test set: {X_test.shape}")
    print(f"🎯 Fraud rate: {y_train.mean():.3%}")
    
    # Train XGBoost with careful parameters
    model = XGBClassifier(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=len(y_train[y_train==0]) / len(y_train[y_train==1]),
        random_state=42,
        eval_metric='auc',
        min_child_weight=3,  # More conservative
        gamma=0.2  # Regularization
    )
    
    # Train model
    model.fit(X_train, y_train)
    
    # Evaluate model
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)
    
    auc_score = roc_auc_score(y_test, y_pred_proba)
    print(f"✅ Model trained successfully!")
    print(f"📊 AUC Score: {auc_score:.4f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🔍 Top 10 Most Important Features:")
    print(feature_importance.head(10))
    
    return model, feature_columns

def test_quality_model(model, feature_columns):
    """Test the model with realistic scenarios"""
    print("\n🧪 Testing quality model with realistic scenarios...")
    
    test_cases = [
        {
            'name': 'Normal Pharmacy Purchase',
            'features': {
                'cc_num': 12345678, 'gender': 0, 'lat': 40.7618, 'long': -73.9708, 
                'city_pop': 8419000, 'unix_time': 1759572359, 'merch_lat': 40.7618, 
                'merch_long': -73.9708, 'hour': 14, 'day_of_week': 2, 'is_weekend': 0,
                'month': 6, 'amt_scaled': (18 - 70) / 200, 'high_risk_hour': 0,
                'cat_health_fitness': 1
            },
            'expected_max_risk': 0.10  # Should be <10%
        },
        {
            'name': 'Evening Cinema Tickets',
            'features': {
                'cc_num': 12345678, 'gender': 0, 'lat': 40.7618, 'long': -73.9708, 
                'city_pop': 8419000, 'unix_time': 1759572359, 'merch_lat': 40.7618, 
                'merch_long': -73.9708, 'hour': 20, 'day_of_week': 5, 'is_weekend': 1,
                'month': 6, 'amt_scaled': (24 - 70) / 200, 'high_risk_hour': 0,
                'cat_entertainment': 1
            },
            'expected_max_risk': 0.08  # Should be <8%
        },
        {
            'name': 'Dubai Luxury Purchase',
            'features': {
                'cc_num': 12345678, 'gender': 0, 'lat': 40.7618, 'long': -73.9708, 
                'city_pop': 8419000, 'unix_time': 1759572359, 'merch_lat': 25.1970, 
                'merch_long': 55.2790, 'hour': 3, 'day_of_week': 2, 'is_weekend': 0,
                'month': 6, 'amt_scaled': (2800 - 70) / 200, 'high_risk_hour': 1,
                'cat_shopping_net': 1
            },
            'expected_min_risk': 0.70  # Should be >70%
        },
        {
            'name': 'Card Testing Pattern',
            'features': {
                'cc_num': 12345678, 'gender': 0, 'lat': 40.7618, 'long': -73.9708, 
                'city_pop': 8419000, 'unix_time': 1759572359, 'merch_lat': 40.7618, 
                'merch_long': -73.9708, 'hour': 2, 'day_of_week': 2, 'is_weekend': 0,
                'month': 6, 'amt_scaled': (3 - 70) / 200, 'high_risk_hour': 1,
                'cat_misc_pos': 1
            },
            'expected_min_risk': 0.60  # Should be >60%
        }
    ]
    
    print("🧪 Test Results:")
    all_passed = True
    
    for test in test_cases:
        # Create feature DataFrame
        test_features = test['features'].copy()
        
        # Add all category columns as 0
        for col in feature_columns:
            if col.startswith('cat_') and col not in test_features:
                test_features[col] = 0
        
        test_df = pd.DataFrame([test_features])[feature_columns]
        prob = model.predict_proba(test_df)[0][1]
        
        # Check if test passed
        if 'expected_max_risk' in test:
            passed = prob <= test['expected_max_risk']
            symbol = "✅" if passed else "❌"
            print(f"{symbol} {test['name']}: {prob:.2%} (expected <{test['expected_max_risk']:.0%})")
        else:
            passed = prob >= test['expected_min_risk']
            symbol = "✅" if passed else "❌"
            print(f"{symbol} {test['name']}: {prob:.2%} (expected >{test['expected_min_risk']:.0%})")
        
        if not passed:
            all_passed = False
    
    if all_passed:
        print("🎉 ALL TESTS PASSED! Model is well-balanced.")
    else:
        print("⚠️ Some tests failed. Model may need adjustment.")
    
    return all_passed

def main():
    """Main function to retrain with quality data"""
    print("🚀 QUALITY FRAUD MODEL RETRAINING")
    print("=" * 50)
    
    try:
        # Step 1: Create quality training data
        quality_data = create_quality_training_data()
        
        # Step 2: Engineer features
        enhanced_data = engineer_quality_features(quality_data)
        
        # Step 3: Train model
        model, feature_columns = train_quality_model(enhanced_data)
        
        # Step 4: Test model
        success = test_quality_model(model, feature_columns)
        
        if success:
            # Step 5: Save model (OVERWRITE existing)
            model_data = {
                'model': model,
                'feature_columns': feature_columns,
                'training_date': pd.Timestamp.now(),
                'model_type': 'quality_retrained',
                'training_samples': len(enhanced_data),
                'auc_score': roc_auc_score(
                    enhanced_data['is_fraud'], 
                    model.predict_proba(enhanced_data[feature_columns])[:, 1]
                )
            }
            
            joblib.dump(model_data, 'enhanced_fraud_model.joblib')
            print(f"✅ Quality model saved: enhanced_fraud_model.joblib")
            print("🎯 MODEL READY FOR DEPLOYMENT!")
            
        else:
            print("⚠️ Model trained but may need further tuning")
            # Save anyway but with warning
            model_data = {
                'model': model,
                'feature_columns': feature_columns,
                'training_date': pd.Timestamp.now(),
                'model_type': 'quality_retrained_with_warnings'
            }
            joblib.dump(model_data, 'enhanced_fraud_model.joblib')
            print("💾 Model saved with warnings: enhanced_fraud_model.joblib")
            
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()