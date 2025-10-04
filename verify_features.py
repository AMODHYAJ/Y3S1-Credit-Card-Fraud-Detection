# verify_features.py - CHECK YOUR COLAB MODEL
import joblib
import pandas as pd

def verify_model_features():
    try:
        model = joblib.load('best_xgb_model_tuned.joblib')
        
        print("🔍 Model Information:")
        print(f"Model type: {type(model).__name__}")
        
        if hasattr(model, 'feature_names_in_'):
            print(f"✅ Model has feature names")
            print(f"Number of features expected: {len(model.feature_names_in_)}")
            print("\n📋 Expected features:")
            for i, feature in enumerate(model.feature_names_in_):
                print(f"{i+1:2d}. {feature}")
        else:
            print("❌ Model doesn't have feature names")
            
        # Test prediction structure
        if hasattr(model, 'feature_names_in_'):
            test_df = pd.DataFrame({col: [0] for col in model.feature_names_in_})
            proba = model.predict_proba(test_df)
            print(f"\n🧪 Test prediction: {proba[0][1]:.4f}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_model_features()