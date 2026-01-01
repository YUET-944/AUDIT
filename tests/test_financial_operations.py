"""
Test suite for financial operations
"""
import pytest
import pandas as pd
from currency_manager import CurrencyManager
from audit_trail import AuditTrail
from database import init_db, get_db_connection

@pytest.fixture
def setup_database():
    """Setup test database"""
    init_db()
    # Run migrations
    import run_migrations
    run_migrations.run_migrations()
    yield
    # Cleanup after tests (in a real scenario, use a test database)

def test_currency_conversion():
    """Test currency conversion functionality"""
    cm = CurrencyManager()
    result = cm.convert_amount(100, 'USD', 'PKR')
    assert isinstance(result, (int, float))

def test_audit_logging():
    """Test audit trail functionality"""
    # Create a test transaction first
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (date, description, category, amount, type)
        VALUES ('2023-01-01', 'Test', 'Income', 100.0, 'Income')
    ''')
    transaction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Log an action
    AuditTrail.log_action('transaction', transaction_id, 'UPDATE', 
                         {'amount': 100}, {'amount': 150}, 1)
    
    logs = AuditTrail.get_audit_log('transaction', transaction_id)
    assert len(logs) > 0
    assert logs[0]['action'] == 'UPDATE'

def test_transaction_crud():
    """Test transaction CRUD operations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create
    cursor.execute('''
        INSERT INTO transactions (date, description, category, amount, type)
        VALUES ('2023-01-01', 'Test', 'Income', 100.0, 'Income')
    ''')
    transaction_id = cursor.lastrowid
    
    # Read
    cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
    result = cursor.fetchone()
    assert result['description'] == 'Test'
    
    # Update
    cursor.execute('''
        UPDATE transactions 
        SET description = 'Updated Test' 
        WHERE id = ?
    ''', (transaction_id,))
    
    cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
    updated = cursor.fetchone()
    assert updated['description'] == 'Updated Test'
    
    # Delete
    cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
    deleted = cursor.fetchone()
    assert deleted is None
    
    conn.close()

if __name__ == "__main__":
    pytest.main([__file__])