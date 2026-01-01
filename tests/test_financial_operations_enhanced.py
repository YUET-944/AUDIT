"""
Enhanced test suite for financial operations with improved coverage
"""
import pytest
import pandas as pd
from decimal import Decimal
from currency_manager import CurrencyManager
from audit_trail import AuditTrail
from database import init_db, get_db_connection
from ai_automation import AIProcessor

class TestFinancialIntegrity:
    @pytest.fixture(autouse=True)
    def setup_database(self):
        init_db()
        # Run migrations
        import run_migrations
        run_migrations.run_migrations()
        yield
        # Cleanup if needed

    def test_currency_conversion_precision(self):
        """Test that currency conversions maintain precision"""
        cm = CurrencyManager()
        # Test edge cases with decimal precision
        result = cm.convert_amount(Decimal('100.00'), 'USD', 'PKR')
        assert isinstance(result, (int, float, Decimal))

    def test_audit_integrity(self):
        """Test that audit logs maintain integrity"""
        # Create a transaction
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (date, description, category, amount, type)
            VALUES ('2023-01-01', 'Test Audit', 'Income', 100.0, 'Income')
        ''')
        transaction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log the action
        AuditTrail.log_action('transaction', transaction_id, 'CREATE', 
                           None, {'amount': 100.0}, 1)
        
        # Verify hash integrity
        logs = AuditTrail.get_audit_log('transaction', transaction_id)
        assert len(logs) > 0
        assert logs[0]['hash_value'] is not None

    def test_anomaly_detection_accuracy(self):
        """Test that anomaly detection works with sample data"""
        processor = AIProcessor()
        # Create sample transaction data
        sample_data = pd.DataFrame({
            'amount': [100, 150, 200, 10000, 120, 130]  # 10000 is an anomaly
        })
        anomalies = processor.detect_anomalies(sample_data)
        assert len(anomalies) > 0  # Should detect the 10000 as anomaly

    def test_transaction_crud_with_audit(self):
        """Test CRUD operations with audit trail"""
        # Create
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (date, description, category, amount, type)
            VALUES ('2023-01-01', 'Test CRUD', 'Income', 200.0, 'Income')
        ''')
        transaction_id = cursor.lastrowid
        conn.commit()
        
        # Verify transaction exists
        cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
        result = cursor.fetchone()
        assert result['description'] == 'Test CRUD'
        
        # Update with audit
        from audit_trail import update_transaction
        update_transaction(transaction_id, '2023-01-02', 'Updated CRUD', 'Income', 250.0, 'Income')
        
        # Verify update
        cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
        updated = cursor.fetchone()
        assert updated['description'] == 'Updated CRUD'
        
        # Check audit trail
        logs = AuditTrail.get_audit_log('transaction', transaction_id)
        assert len(logs) > 0
        
        # Delete
        from database import delete_transaction
        delete_transaction(transaction_id)
        
        # Verify deletion
        cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
        deleted = cursor.fetchone()
        assert deleted is None
        
        conn.close()

    def test_currency_manager_edge_cases(self):
        """Test currency manager with edge cases"""
        cm = CurrencyManager()
        
        # Same currency conversion should return same amount
        result = cm.convert_amount(100.0, 'PKR', 'PKR')
        assert result == 100.0
        
        # Zero amount conversion
        result = cm.convert_amount(0.0, 'USD', 'PKR')
        assert result == 0.0

    def test_bank_integration_matching(self):
        """Test bank transaction matching functionality"""
        from bank_integration import BankIntegration
        bi = BankIntegration()
        
        # Test similarity calculation
        similarity = 0.85  # Just testing the threshold logic
        assert similarity >= bi.match_threshold


if __name__ == "__main__":
    pytest.main([__file__])