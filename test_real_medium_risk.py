# test_real_medium_risk.py
from hybrid_model_manager import get_hybrid_prediction
from unittest.mock import patch
from datetime import datetime

def test_real_medium_risk():
    """Test actual medium risk scenarios that should trigger alerts"""
    print("🧪 TESTING REAL MEDIUM RISK SCENARIOS")
    print("=" * 50)
    
    real_medium_risk_cases = [
        # 🟡 ACTUAL MEDIUM RISK - Borderline cases
        {
            'name': 'Very High Value Local',
            'transaction': {'amount': 1200.0, 'category': 'shopping_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 6.9271, 'lon': 79.8612, 'gender': 'M'},
            'merchant': (6.9280, 79.8620),
            'hour': 14,
            'expected': 'MEDIUM_RISK',  # Should be medium due to very high amount
            'reason': '$1200 is very high for local shopping'
        },
        {
            'name': 'Unusual Category Pattern',
            'transaction': {'amount': 300.0, 'category': 'entertainment', 'card_number': '1234567890123456'},
            'user': {'lat': 6.9271, 'lon': 79.8612, 'gender': 'M'},
            'merchant': (6.9280, 79.8620),
            'hour': 2,  # 2 AM - high risk hours
            'expected': 'MEDIUM_RISK',
            'reason': '$300 entertainment at 2 AM is suspicious'
        },
        {
            'name': 'First Time High Value',
            'transaction': {'amount': 600.0, 'category': 'shopping_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 6.9271, 'lon': 79.8612, 'gender': 'M'},
            'merchant': (6.9300, 79.8600),  # Different area
            'hour': 20,  # 8 PM - evening
            'expected': 'MEDIUM_RISK',
            'reason': 'High value + different area + evening'
        },
    ]
    
    for i, test in enumerate(real_medium_risk_cases, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 40)
        print(f"   {test['reason']}")
        
        with patch('sri_lanka_integration.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, test['hour'], 0, 0)
            mock_datetime.weekday.return_value = 2
            mock_datetime.month.return_value = 1
            
            fraud_prob, risk_level = get_hybrid_prediction(
                test['transaction'],
                test['user'],
                test['merchant'][0], 
                test['merchant'][1]
            )
        
        print(f"   📊 Details: ${test['transaction']['amount']} at {test['hour']}:00")
        print(f"   🎯 Result: {fraud_prob:.2%} → {risk_level}")
        print(f"   ✅ Expected: {test['expected']}")

if __name__ == "__main__":
    test_real_medium_risk()