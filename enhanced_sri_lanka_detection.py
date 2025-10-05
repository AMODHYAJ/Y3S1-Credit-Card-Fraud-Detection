# enhanced_sri_lanka_detection.py
import numpy as np

class EnhancedSriLankaDetector:
    def __init__(self):
        # Sri Lanka with precise boundaries (covers entire country)
        self.sri_lanka_regions = {
            'western': {'min_lat': 6.6, 'max_lat': 7.3, 'min_lon': 79.6, 'max_lon': 80.2},
            'southern': {'min_lat': 5.9, 'max_lat': 6.5, 'min_lon': 80.1, 'max_lon': 81.0},
            'central': {'min_lat': 6.8, 'max_lat': 7.8, 'min_lon': 80.4, 'max_lon': 80.9},
            'northern': {'min_lat': 8.5, 'max_lat': 9.9, 'min_lon': 79.7, 'max_lon': 80.8},
            'eastern': {'min_lat': 7.0, 'max_lat': 8.8, 'min_lon': 81.0, 'max_lon': 81.9},
            'north_central': {'min_lat': 7.8, 'max_lat': 9.0, 'min_lon': 80.2, 'max_lon': 81.0},
            'uva': {'min_lat': 6.5, 'max_lat': 7.5, 'min_lon': 80.9, 'max_lon': 81.5},
            'sabaragamuwa': {'min_lat': 6.4, 'max_lat': 7.2, 'min_lon': 80.2, 'max_lon': 80.8}
        }
        
        # Major cities with coordinates
        self.sri_lanka_cities = {
            'colombo': (6.9271, 79.8612),
            'galle': (6.0535, 80.2210),
            'kandy': (7.2906, 80.6337),
            'jaffna': (9.6615, 80.0255),
            'negombo': (7.2086, 79.8357),
            'matara': (5.9480, 80.5353),
            'anuradhapura': (8.3114, 80.4037),
            'ratnapura': (6.6828, 80.3992),
            'badulla': (6.9895, 81.0557),
            'trincomalee': (8.5874, 81.2152),
            'kalutara': (6.5890, 79.9603),
            'gampaha': (7.0917, 79.9997),
            'kurunegala': (7.4863, 80.3623),
            'puttalam': (8.0362, 79.8283),
            'batticaloa': (7.7167, 81.7000),
            'hambantota': (6.1249, 81.1186)
        }
    
    def is_in_sri_lanka(self, lat, lon):
        """Check if coordinates are anywhere in Sri Lanka"""
        # First check overall country boundaries
        country_bounds = {'min_lat': 5.5, 'max_lat': 10.0, 'min_lon': 79.0, 'max_lon': 82.0}
        
        if not (country_bounds['min_lat'] <= lat <= country_bounds['max_lat'] and
                country_bounds['min_lon'] <= lon <= country_bounds['max_lon']):
            return False
        
        # Then check specific regions (more precise)
        for region, bounds in self.sri_lanka_regions.items():
            if (bounds['min_lat'] <= lat <= bounds['max_lat'] and
                bounds['min_lon'] <= lon <= bounds['max_lon']):
                return True
        
        return True  # If within country bounds, assume Sri Lanka
    
    def get_sri_lanka_city(self, lat, lon):
        """Identify which Sri Lankan city the coordinates are in"""
        for city_name, city_coords in self.sri_lanka_cities.items():
            city_lat, city_lon = city_coords
            distance = np.sqrt((lat - city_lat)**2 + (lon - city_lon)**2)
            if distance < 0.1:  # Within ~11km of city center
                return city_name
        return 'other_sri_lanka'
    
    def get_city_population(self, city_name):
        """Get population for Sri Lankan cities"""
        populations = {
            'colombo': 600000,
            'galle': 100000,
            'kandy': 125000,
            'jaffna': 90000,
            'negombo': 150000,
            'matara': 80000,
            'anuradhapura': 60000,
            'ratnapura': 50000,
            'badulla': 45000,
            'trincomalee': 55000,
            'kalutara': 40000,
            'gampaha': 35000,
            'kurunegala': 30000,
            'other_sri_lanka': 25000  # Default for other areas
        }
        return populations.get(city_name, 25000)