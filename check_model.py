import os
import joblib

def check_model_file():
    print("🔍 Checking model file...")
    
    # Check if file exists
    model_path = 'best_xgb_model_tuned.joblib'
    
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        print("📁 Files in current directory:")
        for file in os.listdir('.'):
            print(f"   - {file}")
        return False
    
    print(f"✅ Model file found: {model_path}")
    
    # Check file size
    file_size = os.path.getsize(model_path) / (1024*1024)  # Size in MB
    print(f"📏 File size: {file_size:.2f} MB")
    
    # Try to load it
    try:
        model = joblib.load(model_path)
        print("✅ Model loaded successfully!")
        print(f"📊 Model type: {type(model)}")
        
        # Try to get some model info
        if hasattr(model, 'get_params'):
            print(f"🔧 Model parameters available")
        
        return True
        
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False

if __name__ == "__main__":
    check_model_file()