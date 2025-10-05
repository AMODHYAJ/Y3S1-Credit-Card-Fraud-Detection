import joblib
import pandas as pd
import numpy as np
import os

class HybridModelManager:
    def __init__(self):
        self.original_model_path = 'enhanced_fraud_model.joblib'
        self.sri_lanka_model_path = 'models/sri_lanka_wide_model.joblib'
        
        # Check model files on initialization
        self.model_status = self.check_model_files()
        for model_name, info in self.model_status.items():
            print(f"{info['status']} - {model_name}")
    
    def check_model_files(self):
        """Check if required model files exist"""
        model_files = {
            'Original Model': 'enhanced_fraud_model.joblib',
            'Sri Lanka Model': 'models/sri_lanka_wide_model.joblib'
        }
        
        status = {}
        for model_name, file_path in model_files.items():
            exists = os.path.exists(file_path)
            status[model_name] = {
                'exists': exists,
                'path': file_path,
                'status': '✅ Available' if exists else '❌ Missing'
            }
        
        return status
    
    def load_hybrid_models(self):
        """Load both models for ensemble prediction"""
        models = {}
        
        # Load original model
        try:
            if os.path.exists(self.original_model_path):
                original_data = joblib.load(self.original_model_path)
                models['original'] = {
                    'model': original_data['model'], 
                    'features': original_data['feature_columns']
                }
                print("✅ Original enhanced model loaded")
            else:
                print("❌ Original model not found at:", self.original_model_path)
                models['original'] = {'model': None, 'features': None}
        except Exception as e:
            print(f"❌ Error loading original model: {e}")
            models['original'] = {'model': None, 'features': None}
        
        # Load Sri Lanka model
        try:
            if os.path.exists(self.sri_lanka_model_path):
                sri_lanka_data = joblib.load(self.sri_lanka_model_path)
                models['sri_lanka'] = {
                    'model': sri_lanka_data['model'], 
                    'features': sri_lanka_data['feature_columns']
                }
                print("✅ Sri Lanka model loaded")
            else:
                print("❌ Sri Lanka model not found at:", self.sri_lanka_model_path)
                models['sri_lanka'] = {'model': None, 'features': None}
        except Exception as e:
            print(f"❌ Error loading Sri Lanka model: {e}")
            models['sri_lanka'] = {'model': None, 'features': None}
        
        return models
    
    def hybrid_predict(self, transaction_data, user_data, merch_lat, merch_lon):
        """Use both models and choose the best prediction"""
        models = self.load_hybrid_models()
        
        # Get predictions from both models
        original_prob = self.predict_with_original(models['original'], transaction_data, user_data, merch_lat, merch_lon)
        sri_lanka_prob = self.predict_with_sri_lanka(models['sri_lanka'], transaction_data, user_data, merch_lat, merch_lon)
        
        print(f"🔍 Hybrid Prediction Analysis:")
        print(f"   Original Model: {original_prob:.2%}")
        print(f"   Sri Lanka Model: {sri_lanka_prob:.2%}")
        
        # Smart selection logic
        final_prob = self.choose_best_prediction(original_prob, sri_lanka_prob, user_data, merch_lat, merch_lon)
        
        # Determine risk level
        if final_prob < 0.1:
            risk_level = 'LOW_RISK'
        elif final_prob < 0.3:
            risk_level = 'MEDIUM_RISK'
        else:
            risk_level = 'HIGH_RISK'
        
        print(f"   Final Decision: {final_prob:.2%} → {risk_level}")
        return final_prob, risk_level
    
    def choose_best_prediction(self, original_prob, sri_lanka_prob, user_data, merch_lat, merch_lon):
        """Choose the best prediction based on context"""
        user_lat = user_data.get('lat', 40.7618)
        user_lon = user_data.get('lon', -73.9708)
        
        # Calculate if transaction is in Sri Lanka
        is_sri_lanka_user = self.is_in_sri_lanka(user_lat, user_lon)
        is_sri_lanka_merchant = self.is_in_sri_lanka(merch_lat, merch_lon)
        is_sri_lanka_transaction = is_sri_lanka_user or is_sri_lanka_merchant
        
        # Calculate geographic distance
        geo_distance = np.sqrt((user_lat - merch_lat)**2 + (user_lon - merch_lon)**2)
        is_local_sri_lanka = is_sri_lanka_transaction and (geo_distance < 0.1)
        
        print(f"   Context Analysis:")
        print(f"     - User in Sri Lanka: {is_sri_lanka_user}")
        print(f"     - Merchant in Sri Lanka: {is_sri_lanka_merchant}")
        print(f"     - Local Sri Lanka transaction: {is_local_sri_lanka}")
        print(f"     - Geographic distance: {geo_distance:.4f}°")
        
        # Decision logic
        if is_local_sri_lanka:
            # For local Sri Lanka transactions, trust Sri Lanka model more
            if abs(original_prob - sri_lanka_prob) > 0.3:  # Big difference
                print("   🤖 Strategy: Using Sri Lanka model (strong local transaction pattern)")
                return sri_lanka_prob
            else:
                # Average if predictions are close
                weighted_avg = (original_prob * 0.3) + (sri_lanka_prob * 0.7)
                print("   🤖 Strategy: Weighted average (70% Sri Lanka, 30% Original)")
                return weighted_avg
        elif is_sri_lanka_transaction:
            # For Sri Lanka but not local, balanced approach
            weighted_avg = (original_prob * 0.5) + (sri_lanka_prob * 0.5)
            print("   🤖 Strategy: Balanced average (50% each model)")
            return weighted_avg
        else:
            # For international/non-Sri-Lanka, trust original model
            print("   🤖 Strategy: Using original model (international transaction)")
            return original_prob
    
    def is_in_sri_lanka(self, lat, lon):
        """Check if coordinates are in Sri Lanka"""
        # Sri Lanka approximate boundaries
        sri_lanka_bounds = {
            'min_lat': 5.5, 'max_lat': 10.0,
            'min_lon': 79.0, 'max_lon': 82.0
        }
        
        return (sri_lanka_bounds['min_lat'] <= lat <= sri_lanka_bounds['max_lat'] and
                sri_lanka_bounds['min_lon'] <= lon <= sri_lanka_bounds['max_lon'])
    
    def predict_with_original(self, model_data, transaction_data, user_data, merch_lat, merch_lon):
        """Predict using original model"""
        if model_data['model'] is None:
            print("   ⚠️  Original model not available, using fallback")
            return self.get_fallback_prediction(transaction_data)[0]  # Return probability only
        
        try:
            # Try to use your existing feature transformer
            from feature_transformer import FraudFeatureTransformer
            transformer = FraudFeatureTransformer()
            features_df = transformer.transform_transaction(transaction_data, user_data, merch_lat, merch_lon)
            
            # Ensure feature compatibility
            if model_data['features']:
                for col in model_data['features']:
                    if col not in features_df.columns:
                        features_df[col] = 0
                features_df = features_df[model_data['features']]
            
            prob = model_data['model'].predict_proba(features_df)[0][1]
            return prob
            
        except Exception as e:
            print(f"   ⚠️  Original model prediction failed: {e}")
            return self.get_fallback_prediction(transaction_data)[0]
    
    def predict_with_sri_lanka(self, model_data, transaction_data, user_data, merch_lat, merch_lon):
        """Predict using Sri Lanka model"""
        if model_data['model'] is None:
            print("   ⚠️  Sri Lanka model not available, using fallback")
            return self.get_fallback_prediction(transaction_data)[0]  # Return probability only
        
        try:
            # Use Sri Lanka feature transformer
            from sri_lanka_integration import SriLankaFeatureTransformer
            transformer = SriLankaFeatureTransformer()
            features_df = transformer.transform_transaction(transaction_data, user_data, merch_lat, merch_lon)
            
            # Ensure feature compatibility
            if model_data['features']:
                for col in model_data['features']:
                    if col not in features_df.columns:
                        features_df[col] = 0
                features_df = features_df[model_data['features']]
            
            prob = model_data['model'].predict_proba(features_df)[0][1]
            return prob
            
        except Exception as e:
            print(f"   ⚠️  Sri Lanka model prediction failed: {e}")
            return self.get_fallback_prediction(transaction_data)[0]
    
    def get_fallback_prediction(self, transaction_data):
        """Fallback prediction when models fail"""
        amount = transaction_data.get('amount', 0)
        
        # Simple rule-based fallback
        if amount > 2000:
            return 0.85, 'HIGH_RISK'
        elif amount > 1000:
            return 0.65, 'MEDIUM_RISK'
        elif amount < 10:
            return 0.80, 'HIGH_RISK'  # Small amounts can be card testing
        else:
            return 0.15, 'LOW_RISK'

# Global instance
_hybrid_manager = HybridModelManager()

def get_hybrid_prediction(transaction_data, user_data, merch_lat, merch_lon):
    """Main function to get hybrid prediction with comprehensive error handling"""
    try:
        return _hybrid_manager.hybrid_predict(transaction_data, user_data, merch_lat, merch_lon)
    except Exception as e:
        print(f"❌ Hybrid system failed: {e}")
        print("🔄 Using fallback prediction system")
        return _hybrid_manager.get_fallback_prediction(transaction_data)