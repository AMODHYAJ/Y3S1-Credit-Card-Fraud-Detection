# test_all_sri_lanka.py
from hybrid_model_manager import get_hybrid_prediction

def test_sri_lanka_locations():
    """Test transactions from various Sri Lanka locations"""
    print("🧪 TESTING ALL SRI LANKA LOCATIONS")
    print("=" * 50)
    
    sri_lanka_locations = [
        # Format: (Location Name, lat, lon)
        ("Colombo", 6.9271, 79.8612),
        ("Galle", 6.0535, 80.2210),
        ("Kandy", 7.2906, 80.6337),
        ("Jaffna", 9.6615, 80.0255),
        ("Negombo", 7.2086, 79.8357),
        ("Matara", 5.9480, 80.5353),
        ("Anuradhapura", 8.3114, 80.4037),
        ("Ratnapura", 6.6828, 80.3992),
        ("Badulla", 6.9895, 81.0557),
        ("Trincomalee", 8.5874, 81.2152),
        ("Hambantota", 6.1249, 81.1186),
        ("Kalutara", 6.5890, 79.9603),
        ("Kurunegala", 7.4863, 80.3623),
        ("Batticaloa", 7.7167, 81.7000),
        ("Small Village (Central)", 7.3, 80.5),  # Random village
        ("Coastal Area (East)", 7.8, 81.5),      # Random coastal area
    ]
    
    for location_name, lat, lon in sri_lanka_locations:
        print(f"\n📍 Testing: {location_name} ({lat:.4f}, {lon:.4f})")
        print("-" * 40)
        
        # Test local grocery transaction
        transaction = {'amount': 25.0, 'category': 'grocery_pos', 'card_number': '1234567890123456'}
        user_data = {'lat': lat, 'lon': lon, 'gender': 'M'}
        
        # Local merchant (very close)
        merchant_lat = lat + 0.001  # ~100 meters away
        merchant_lon = lon + 0.001
        
        fraud_prob, risk_level = get_hybrid_prediction(
            transaction, user_data, merchant_lat, merchant_lon
        )
        
        print(f"   Local Grocery: {fraud_prob:.2%} → {risk_level}")
        
        # Also test with merchant in different Sri Lanka city
        if location_name == "Colombo":
            different_merchant = (6.0535, 80.2210)  # Galle
        else:
            different_merchant = (6.9271, 79.8612)  # Colombo
            
        fraud_prob2, risk_level2 = get_hybrid_prediction(
            transaction, user_data, different_merchant[0], different_merchant[1]
        )
        
        print(f"   Different City: {fraud_prob2:.2%} → {risk_level2}")

if __name__ == "__main__":
    test_sri_lanka_locations()