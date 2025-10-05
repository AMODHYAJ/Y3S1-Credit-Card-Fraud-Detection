# test_sri_lanka_risks.py
from hybrid_model_manager import get_hybrid_prediction

def test_sri_lanka_risk_levels():
    """Test medium and high risk scenarios within Sri Lanka"""
    print("🧪 TESTING SRI LANKA MEDIUM & HIGH RISK SCENARIOS")
    print("=" * 60)
    
    risk_test_cases = [
        # 🔴 HIGH RISK PATTERNS WITHIN SRI LANKA
        {
            'name': 'Colombo Card Testing Fraud',
            'transaction': {'amount': 2.0, 'category': 'grocery_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 6.9271, 'lon': 79.8612, 'gender': 'M'},
            'merchant': (6.9280, 79.8620),  # Local Colombo
            'hour': 3,  # 3 AM - unusual hours
            'expected_risk': 'HIGH_RISK',
            'reason': 'Card testing pattern: $2 transaction at 3 AM'
        },
        {
            'name': 'Galle High-Value Fraud', 
            'transaction': {'amount': 800.0, 'category': 'shopping_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 6.0535, 'lon': 80.2210, 'gender': 'F'},
            'merchant': (6.0540, 80.2220),  # Local Galle
            'hour': 1,  # 1 AM - unusual hours
            'expected_risk': 'HIGH_RISK',
            'reason': 'High value + unusual hours: $800 at 1 AM'
        },
        {
            'name': 'Kandy Rapid Succession Fraud',
            'transaction': {'amount': 5.0, 'category': 'grocery_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 7.2906, 'lon': 80.6337, 'gender': 'M'},
            'merchant': (7.2910, 80.6340),  # Local Kandy
            'hour': 4,  # 4 AM - high risk hours
            'expected_risk': 'HIGH_RISK', 
            'reason': 'Small amount + high risk hours: potential card testing'
        },
        
        # 🟡 MEDIUM RISK PATTERNS WITHIN SRI LANKA
        {
            'name': 'Colombo High-Value Legit',
            'transaction': {'amount': 450.0, 'category': 'shopping_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 6.9271, 'lon': 79.8612, 'gender': 'M'},
            'merchant': (6.9300, 79.8600),  # Colombo different area
            'hour': 15,  # Normal business hours
            'expected_risk': 'MEDIUM_RISK',
            'reason': 'High value but normal hours: requires verification'
        },
        {
            'name': 'Galle Inter-City Travel',
            'transaction': {'amount': 120.0, 'category': 'travel', 'card_number': '1234567890123456'},
            'user': {'lat': 6.0535, 'lon': 80.2210, 'gender': 'F'},
            'merchant': (6.9271, 79.8612),  # Colombo (different city)
            'hour': 10,  # Normal hours
            'expected_risk': 'MEDIUM_RISK',
            'reason': 'Inter-city travel: Galle to Colombo'
        },
        {
            'name': 'Late Night Legit Purchase',
            'transaction': {'amount': 65.0, 'category': 'misc_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 6.9271, 'lon': 79.8612, 'gender': 'M'},
            'merchant': (6.9280, 79.8620),  # Local Colombo
            'hour': 23,  # 11 PM - late but not extreme
            'expected_risk': 'MEDIUM_RISK',
            'reason': 'Late night medium-value transaction'
        },
        
        # 🟢 LOW RISK PATTERNS (for comparison)
        {
            'name': 'Normal Colombo Grocery',
            'transaction': {'amount': 25.0, 'category': 'grocery_pos', 'card_number': '1234567890123456'},
            'user': {'lat': 6.9271, 'lon': 79.8612, 'gender': 'M'},
            'merchant': (6.9280, 79.8620),  # Local Colombo
            'hour': 14,  # Normal afternoon
            'expected_risk': 'LOW_RISK',
            'reason': 'Normal local grocery shopping'
        }
    ]
    
    for i, test in enumerate(risk_test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 50)
        print(f"   Reason: {test['reason']}")
        
        # Override the current hour for testing
        import datetime
        original_datetime = __import__('datetime').datetime
        class MockDateTime:
            @staticmethod
            def now():
                return original_datetime(2024, 1, 1, test['hour'], 0, 0)
            @staticmethod  
            def weekday():
                return 2  # Tuesday
            @staticmethod
            def month():
                return 1  # January
        
        # Mock datetime for consistent testing
        import sri_lanka_integration
        original_datetime_module = sri_lanka_integration.datetime
        sri_lanka_integration.datetime = MockDateTime
        
        fraud_prob, risk_level = get_hybrid_prediction(
            test['transaction'],
            test['user'],
            test['merchant'][0], 
            test['merchant'][1]
        )
        
        # Restore original datetime
        sri_lanka_integration.datetime = original_datetime_module
        
        status = "✅ PASS" if risk_level == test['expected_risk'] else "❌ FAIL"
        risk_emoji = "🔴" if risk_level == "HIGH_RISK" else "🟡" if risk_level == "MEDIUM_RISK" else "🟢"
        
        print(f"   {risk_emoji} Result: {fraud_prob:.2%} → {risk_level}")
        print(f"   {status} Expected: {test['expected_risk']}")
        
        # Show risk factors
        print(f"   📊 Risk Factors:")
        print(f"      - Amount: ${test['transaction']['amount']}")
        print(f"      - Hour: {test['hour']}:00")
        print(f"      - Category: {test['transaction']['category']}")
        print(f"      - Location: {'Local' if test['merchant'][0] == test['user']['lat'] else 'Inter-city'}")

if __name__ == "__main__":
    test_sri_lanka_risk_levels()