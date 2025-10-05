# test_sri_lanka_risks_fixed.py
from hybrid_model_manager import get_hybrid_prediction
from unittest.mock import patch
from datetime import datetime

def test_sri_lanka_risk_levels_fixed():
    """Test medium and high risk scenarios with proper hour mocking"""
    print("🧪 TESTING SRI LANKA RISKS WITH PROPER HOUR MOCKING")
    print("=" * 60)
    
    risk_test_cases = [
        # 🔴 HIGH RISK PATTERNS WITHIN SRI LANKA
        {
            'name': 'Colombo Card Testing Fraud',
            'transaction': {'amount': 2.0, 'category': 'grocery_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 6.9271, 'lon': 79.8612, 'gender': 'M'},
            'merchant': (6.9280, 79.8620),
            'hour': 3,  # 3 AM - unusual hours
            'expected_risk': 'HIGH_RISK',
            'reason': 'Card testing pattern: $2 transaction at 3 AM'
        },
        {
            'name': 'Galle High-Value Fraud', 
            'transaction': {'amount': 800.0, 'category': 'shopping_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 6.0535, 'lon': 80.2210, 'gender': 'F'},
            'merchant': (6.0540, 80.2220),
            'hour': 1,  # 1 AM - unusual hours
            'expected_risk': 'HIGH_RISK',
            'reason': 'High value + unusual hours: $800 at 1 AM'
        },
        
        # 🟡 MEDIUM RISK PATTERNS WITHIN SRI LANKA (ADJUSTED EXPECTATIONS)
        {
            'name': 'Colombo High-Value Legit',
            'transaction': {'amount': 250.0, 'category': 'shopping_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 6.9271, 'lon': 79.8612, 'gender': 'M'},
            'merchant': (6.9300, 79.8600),
            'hour': 15,  # Normal business hours
            'expected_risk': 'MEDIUM_RISK',
            'reason': 'High value but normal hours: requires verification'
        },
        {
            'name': 'Galle Inter-City Travel',
            'transaction': {'amount': 80.0, 'category': 'travel', 'card_number': '1234567890123456'},
            'user': {'lat': 6.0535, 'lon': 80.2210, 'gender': 'F'},
            'merchant': (6.9271, 79.8612),  # Colombo (different city)
            'hour': 10,  # Normal hours
            'expected_risk': 'MEDIUM_RISK',
            'reason': 'Inter-city travel: Galle to Colombo'
        },
        {
            'name': 'Late Night Legit Purchase',
            'transaction': {'amount': 45.0, 'category': 'misc_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 6.9271, 'lon': 79.8612, 'gender': 'M'},
            'merchant': (6.9280, 79.8620),
            'hour': 22,  # 10 PM - late but not extreme
            'expected_risk': 'MEDIUM_RISK',
            'reason': 'Late night medium-value transaction'
        },
    ]
    
    for i, test in enumerate(risk_test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 50)
        print(f"   Reason: {test['reason']}")
        
        # Mock datetime properly
        with patch('sri_lanka_integration.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, test['hour'], 0, 0)
            mock_datetime.weekday.return_value = 2  # Tuesday
            mock_datetime.month.return_value = 1    # January
            
            fraud_prob, risk_level = get_hybrid_prediction(
                test['transaction'],
                test['user'],
                test['merchant'][0], 
                test['merchant'][1]
            )
        
        status = "✅ PASS" if risk_level == test['expected_risk'] else "❌ FAIL"
        risk_emoji = "🔴" if risk_level == "HIGH_RISK" else "🟡" if risk_level == "MEDIUM_RISK" else "🟢"
        
        print(f"   {risk_emoji} Result: {fraud_prob:.2%} → {risk_level}")
        print(f"   {status} Expected: {test['expected_risk']}")
        
        # Show detailed analysis
        print(f"   📊 Transaction Details:")
        print(f"      - Amount: ${test['transaction']['amount']}")
        print(f"      - Actual Hour: {test['hour']}:00")
        print(f"      - Category: {test['transaction']['category']}")
        print(f"      - High Risk Hours: {test['hour'] in [2,3,4,22,23,0]}")

if __name__ == "__main__":
    test_sri_lanka_risk_levels_fixed()