"""
Bank integration and reconciliation module
"""
import difflib
from database import get_db_connection

class BankIntegration:
    def __init__(self):
        self.match_threshold = 0.8  # 80% similarity for matching
    
    def import_bank_transactions(self, bank_account_id, transactions_data):
        """Import transactions from bank"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for tx in transactions_data:
            cursor.execute('''
                INSERT OR IGNORE INTO bank_transactions
                (bank_account_id, external_transaction_id, date, description, amount, currency_code)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                bank_account_id,
                tx.get('external_id'),
                tx.get('date'),
                tx.get('description'),
                tx.get('amount'),
                tx.get('currency', 'PKR')
            ))
        
        conn.commit()
        conn.close()
    
    def find_matches(self, bank_tx_id):
        """Find potential matches for a bank transaction"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the bank transaction
        cursor.execute('SELECT * FROM bank_transactions WHERE id = ?', (bank_tx_id,))
        bank_tx = cursor.fetchone()
        
        # Find potential matches in our transactions
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE date = ? AND ABS(amount - ?) < 1.0  -- Small tolerance for rounding
        ''', (bank_tx['date'], bank_tx['amount']))
        
        potential_matches = cursor.fetchall()
        
        matches = []
        for tx in potential_matches:
            similarity = difflib.SequenceMatcher(None, bank_tx['description'], tx['description']).ratio()
            if similarity >= self.match_threshold:
                matches.append({
                    'transaction': tx,
                    'similarity': similarity
                })
        
        conn.close()
        return sorted(matches, key=lambda x: x['similarity'], reverse=True)
    
    def reconcile_transaction(self, bank_tx_id, internal_tx_id):
        """Reconcile a bank transaction with an internal transaction"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE bank_transactions 
            SET status = 'reconciled', matched_transaction_id = ?
            WHERE id = ?
        ''', (internal_tx_id, bank_tx_id))
        
        conn.commit()
        conn.close()