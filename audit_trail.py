"""
Immutable audit trail module
"""
import hashlib
import json
from datetime import datetime
from database import get_db_connection

class AuditTrail:
    @staticmethod
    def log_action(entity_type, entity_id, action, old_values=None, new_values=None, user_id=None):
        """Log an action to the audit trail"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create hash for immutability
        data_to_hash = f"{entity_type}{entity_id}{action}{old_values}{new_values}{user_id}{datetime.now().isoformat()}"
        hash_value = hashlib.sha256(data_to_hash.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO audit_logs 
            (entity_type, entity_id, action, old_values, new_values, user_id, hash_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            entity_type,
            entity_id,
            action,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            user_id,
            hash_value
        ))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_audit_log(entity_type, entity_id):
        """Retrieve audit log for an entity"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM audit_logs 
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY timestamp DESC
        ''', (entity_type, entity_id))
        
        results = cursor.fetchall()
        conn.close()
        return results

# Integration with existing functions
def update_transaction(trans_id, date, description, category, amount, trans_type):
    """Update transaction with audit logging"""
    # Get old values for audit
    old_values = get_transaction_by_id(trans_id)
    
    # Perform update
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE transactions
        SET date = ?, description = ?, category = ?, amount = ?, type = ?
        WHERE id = ?
    ''', (date, description, category, amount, trans_type, trans_id))
    conn.commit()
    conn.close()
    
    # Log the change
    new_values = {
        'date': date,
        'description': description,
        'category': category,
        'amount': amount,
        'type': trans_type
    }
    
    AuditTrail.log_action('transaction', trans_id, 'UPDATE', old_values, new_values)

def get_transaction_by_id(trans_id):
    """Helper function to get transaction by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions WHERE id = ?', (trans_id,))
    result = cursor.fetchone()
    conn.close()
    return result