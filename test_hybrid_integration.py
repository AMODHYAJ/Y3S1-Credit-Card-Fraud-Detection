# test_hybrid_integration.py
from hybrid_model_manager import get_hybrid_prediction

def test_hybrid_system():
    """Test the hybrid system with various scenarios"""
    print("🧪 TESTING HYBRID FRAUD DETECTION SYSTEM")
    print("=" * 50)
    
    test_cases = [
        {
            'name': 'Galle Cargills (Local Sri Lanka)',
            'transaction': {'amount': 15.0, 'category': 'grocery_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 6.0535, 'lon': 80.2210, 'gender': 'M'},
            'merchant': (6.0540, 80.2200),  # Galle Cargills
            'expected_risk': 'LOW_RISK'
        },
        {
            'name': 'Dubai Luxury (International)',
            'transaction': {'amount': 2800.0, 'category': 'shopping_net', 'card_number': '1234567890123456'},
            'user': {'lat': 6.9271, 'lon': 79.8612, 'gender': 'M'},  # Colombo user
            'merchant': (25.1997, 55.2795),  # Dubai
            'expected_risk': 'HIGH_RISK'
        },
        {
            'name': 'Colombo Restaurant (Local Sri Lanka)',
            'transaction': {'amount': 35.0, 'category': 'food_dining', 'card_number': '1234567890123456'},
            'user': {'lat': 6.9271, 'lon': 79.8612, 'gender': 'F'},
            'merchant': (6.9280, 79.8620),  # Colombo restaurant
            'expected_risk': 'LOW_RISK'
        },
        {
            'name': 'NY Local (Original Pattern)',
            'transaction': {'amount': 85.0, 'category': 'grocery_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 40.7618, 'lon': -73.9708, 'gender': 'M'},
            'merchant': (40.7618, -73.9708),  # Same location
            'expected_risk': 'LOW_RISK'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 40)
        
        fraud_prob, risk_level = get_hybrid_prediction(
            test['transaction'],
            test['user'], 
            test['merchant'][0],
            test['merchant'][1]
        )
        
        status = "✅ PASS" if risk_level == test['expected_risk'] else "❌ FAIL"
        print(f"{status} Expected: {test['expected_risk']}, Got: {risk_level} ({fraud_prob:.2%})")

if __name__ == "__main__":
    test_hybrid_system()