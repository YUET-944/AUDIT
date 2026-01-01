"""
Currency management module for multi-currency support
"""
import requests
from datetime import datetime
from database import get_db_connection

class CurrencyManager:
    def __init__(self):
        self.base_currency = 'PKR'
    
    def get_exchange_rate(self, from_currency, to_currency):
        """Get exchange rate from external API"""
        # Using exchangerate-api.com as example
        try:
            response = requests.get(f"https://api.exchangerate-api.com/v4/latest/{from_currency}")
            rates = response.json().get('rates', {})
            return rates.get(to_currency, 1.0)
        except:
            # Fallback to cached rate or 1.0
            return 1.0
    
    def convert_amount(self, amount, from_currency, to_currency):
        """Convert amount between currencies"""
        if from_currency == to_currency:
            return amount
        
        rate = self.get_exchange_rate(from_currency, to_currency)
        return amount * rate
    
    def add_transaction_with_currency(self, date, description, category, amount, 
                                   trans_type, currency_code='PKR'):
        """Add transaction with currency conversion"""
        base_amount = self.convert_amount(amount, currency_code, self.base_currency)
        rate = base_amount / amount if amount != 0 else 1.0
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions 
            (date, description, category, amount, type, currency_code, base_currency_amount, exchange_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, description, category, amount, trans_type, currency_code, base_amount, rate))
        conn.commit()
        conn.close()