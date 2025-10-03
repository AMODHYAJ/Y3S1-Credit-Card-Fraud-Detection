import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

class FraudAnalytics:
    def __init__(self):
        self.transactions = self.load_transactions()
        self.fraud_alerts = self.load_fraud_alerts()
    
    def load_transactions(self):
        try:
            with open('data/transactions.json', 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def load_fraud_alerts(self):
        try:
            with open('data/fraud_alerts.json', 'r') as f:
                return json.load(f)
        except:
            return []
    
    def get_daily_fraud_trends(self, days=30):
        """Analyze fraud trends over time"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        daily_counts = {}
        for alert in self.fraud_alerts:
            try:
                alert_date = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
                if start_date <= alert_date <= end_date:
                    date_str = alert_date.strftime('%Y-%m-%d')
                    daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
            except:
                continue
        
        return daily_counts
    
    def create_fraud_heatmap(self):
        """Create geographic fraud heatmap"""
        locations = []
        for alert in self.fraud_alerts:
            if 'transaction_data' in alert:
                tx_data = alert['transaction_data']
                if tx_data.get('merch_lat') and tx_data.get('merch_lon'):
                    locations.append({
                        'lat': tx_data['merch_lat'],
                        'lon': tx_data['merch_lon'],
                        'amount': tx_data['amount'],
                        'probability': alert['fraud_probability']
                    })
        
        return locations
    
    def calculate_performance_metrics(self):
        """Calculate key performance indicators"""
        total_alerts = len(self.fraud_alerts)
        resolved_alerts = len([a for a in self.fraud_alerts if a['status'] == 'resolved'])
        high_risk_alerts = len([a for a in self.fraud_alerts if a.get('priority') == 'HIGH'])
        
        avg_fraud_amount = 0
        if self.fraud_alerts:
            avg_fraud_amount = sum(a['amount'] for a in self.fraud_alerts) / len(self.fraud_alerts)
        
        return {
            'total_alerts': total_alerts,
            'resolved_alerts': resolved_alerts,
            'resolution_rate': (resolved_alerts / total_alerts * 100) if total_alerts > 0 else 0,
            'high_risk_alerts': high_risk_alerts,
            'avg_fraud_amount': avg_fraud_amount,
            'total_fraud_amount': sum(a['amount'] for a in self.fraud_alerts)
        }