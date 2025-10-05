# setup_deployment.py - UPDATED FOR HYBRID MODEL SYSTEM
import os
import json
import sys

def setup_deployment_environment():
    """Setup everything needed for deployment with hybrid model system"""
    print("🚀 Setting up deployment environment for Hybrid ML System...")
    
    # Create necessary directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('utils', exist_ok=True)
    
    # Test hybrid model system instead of single model manager
    try:
        from hybrid_model_manager import HybridModelManager
        manager = HybridModelManager()
        models = manager.load_hybrid_models()
        
        # Count available models
        available_models = sum(1 for model_data in models.values() if model_data['model'] is not None)
        print(f"✅ Hybrid model system initialized")
        print(f"📊 Models loaded: {available_models}/2")
        
        if available_models == 0:
            print("⚠️ Warning: No ML models found. System will use fallback rules.")
            print("💡 Please ensure these model files exist:")
            print("   - enhanced_fraud_model.joblib (Original model)")
            print("   - models/sri_lanka_wide_model.joblib (Sri Lanka model)")
        
    except Exception as e:
        print(f"⚠️ Hybrid model initialization warning: {e}")
        print("🔄 System will use rule-based fallback detection")
        
        # Manual model file check
        print("🔍 Manual model file check:")
        model_files = {
            'Original Model': 'enhanced_fraud_model.joblib',
            'Sri Lanka Model': 'models/sri_lanka_wide_model.joblib'
        }
        
        for model_name, file_path in model_files.items():
            exists = os.path.exists(file_path)
            status = '✅ Available' if exists else '❌ Missing'
            print(f"   {status} - {model_name}")
    
    # Create basic data files if they don't exist
    data_files = {
        'data/users.json': {},
        'data/transactions.json': {},
        'data/pending_approvals.json': [],
        'data/fraud_alerts.json': []
    }
    
    for file_path, default_data in data_files.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=2)
            print(f"✅ Created {file_path}")
    
    # Check for required feature transformers
    try:
        from feature_transformer import FraudFeatureTransformer
        print("✅ Original feature transformer available")
    except ImportError:
        print("⚠️ Original feature transformer not found")
    
    try:
        from sri_lanka_integration import SriLankaFeatureTransformer
        print("✅ Sri Lanka feature transformer available")
    except ImportError:
        print("⚠️ Sri Lanka feature transformer not found")
    
    print("🎉 Hybrid ML deployment environment ready!")

if __name__ == "__main__":
    setup_deployment_environment()