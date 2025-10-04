# setup_deployment.py
import os
import sys
from model_manager import ModelManager

def setup_deployment_environment():
    """Setup everything needed for deployment"""
    print("🚀 Setting up deployment environment...")
    
    # Create necessary directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('utils', exist_ok=True)
    
    # Initialize model manager and ensure model exists
    manager = ModelManager()
    model_data = manager.load_or_create_model()
    
    print("✅ Deployment environment ready!")
    print(f"📁 Model type: {model_data.get('model_type', 'standalone')}")
    
    # Create basic data files if they don't exist
    import json
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

if __name__ == "__main__":
    setup_deployment_environment()