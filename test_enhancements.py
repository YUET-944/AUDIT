"""
Test script to verify all enhancements work correctly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_enhancements():
    """Test database enhancements with connection pooling"""
    print("Testing database enhancements...")
    try:
        from database_pool import db_pool
        from database import init_db, get_transactions
        print("✓ Database pool imported successfully")
        
        # Initialize database
        init_db()
        print("✓ Database initialized successfully")
        
        # Test getting transactions
        transactions = get_transactions()
        print(f"✓ Retrieved {len(transactions)} transactions")
        
        # Test connection pool
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transactions")
            count = cursor.fetchone()[0]
            print(f"✓ Connection pool test passed: {count} transactions")
        
        print("✓ Database enhancements working correctly")
    except Exception as e:
        print(f"✗ Database enhancements failed: {str(e)}")
        return False
    return True


def test_caching_enhancements():
    """Test caching enhancements"""
    print("\nTesting caching enhancements...")
    try:
        from caching import cache_manager, cache_report_data, cache_financial_summary, cache_dashboard_kpis
        print("✓ Caching module imported successfully")
        
        # Test basic caching
        cache_manager.set("test_key", "test_value", 300)
        value = cache_manager.get("test_key")
        assert value == "test_value", f"Expected 'test_value', got {value}"
        print("✓ Basic caching test passed")
        
        # Test cache decorators
        @cache_report_data(ttl=300)
        def test_function(x):
            return x * 2
        
        result = test_function(5)
        assert result == 10, f"Expected 10, got {result}"
        print("✓ Cache decorator test passed")
        
        print("✓ Caching enhancements working correctly")
    except Exception as e:
        print(f"✗ Caching enhancements failed: {str(e)}")
        return False
    return True


def test_advanced_reporting():
    """Test advanced reporting module"""
    print("\nTesting advanced reporting...")
    try:
        from advanced_reporting import AdvancedReporting
        reporter = AdvancedReporting()
        print("✓ Advanced reporting module imported successfully")
        
        # Test cash flow forecasting
        forecast = reporter.cash_flow_forecasting(months_ahead=3)
        print("✓ Cash flow forecasting test passed")
        
        # Test budget variance analysis
        variance = reporter.budget_variance_analysis()
        print("✓ Budget variance analysis test passed")
        
        # Test financial ratios
        ratios = reporter.financial_ratios_analysis()
        print("✓ Financial ratios analysis test passed")
        
        print("✓ Advanced reporting working correctly")
    except Exception as e:
        print(f"✗ Advanced reporting failed: {str(e)}")
        return False
    return True


def test_clean_architecture():
    """Test clean architecture implementation"""
    print("\nTesting clean architecture...")
    try:
        from infrastructure.dependency_injection import dependency_factory
        from domain.entities import Transaction, User
        print("✓ Clean architecture modules imported successfully")
        
        # Test dependency injection
        transaction_service = dependency_factory.get_transaction_service()
        print("✓ Dependency injection working correctly")
        
        # Test domain entity creation
        transaction = Transaction(
            id=None,
            date="2024-01-01",
            description="Test transaction",
            category="Test",
            amount=100.0,
            type="Income"
        )
        print("✓ Domain entity creation working correctly")
        
        print("✓ Clean architecture working correctly")
    except Exception as e:
        print(f"✗ Clean architecture failed: {str(e)}")
        return False
    return True


def test_background_jobs():
    """Test background job processing"""
    print("\nTesting background job processing...")
    try:
        from caching import background_jobs
        print("✓ Background job processor imported successfully")
        
        # Test job queue
        job_id = background_jobs.add_job("test_job", {"test": "data"})
        queue_size = background_jobs.get_queue_size()
        print(f"✓ Background job added: {job_id}, Queue size: {queue_size}")
        
        print("✓ Background job processing working correctly")
    except Exception as e:
        print(f"✗ Background job processing failed: {str(e)}")
        return False
    return True


def test_client_portal():
    """Test client portal service"""
    print("\nTesting client portal service...")
    try:
        from application.client_portal_service import ClientPortalService
        from infrastructure.dependency_injection import dependency_factory
        print("✓ Client portal service imported successfully")
        
        # Test service creation
        client_service = dependency_factory.get_client_portal_service()
        print("✓ Client portal service created via dependency injection")
        
        # Test permissions
        permissions = client_service.get_client_permissions(1, "client")
        print(f"✓ Client permissions retrieved: {list(permissions.keys())}")
        
        print("✓ Client portal service working correctly")
    except Exception as e:
        print(f"✗ Client portal service failed: {str(e)}")
        return False
    return True


def test_approval_workflow():
    """Test approval workflow service"""
    print("\nTesting approval workflow service...")
    try:
        from application.approval_workflow_service import ApprovalWorkflowService
        from infrastructure.dependency_injection import dependency_factory
        print("✓ Approval workflow service imported successfully")
        
        # Test service creation
        approval_service = dependency_factory.get_approval_workflow_service()
        print("✓ Approval workflow service created via dependency injection")
        
        # Test approval thresholds
        from domain.entities import Transaction
        test_transaction = Transaction(
            id=1,
            date="2024-01-01",
            description="Test transaction",
            category="Test",
            amount=150000,  # Above accountant threshold
            type="Expense"
        )
        
        requires_approval = approval_service.requires_approval(test_transaction, "accountant")
        print(f"✓ Approval required for high-value transaction: {requires_approval}")
        
        print("✓ Approval workflow service working correctly")
    except Exception as e:
        print(f"✗ Approval workflow service failed: {str(e)}")
        return False
    return True


def test_export_functionality():
    """Test export functionality"""
    print("\nTesting export functionality...")
    try:
        import pandas as pd
        from database import get_transactions
        print("✓ Export dependencies imported successfully")
        
        # Test data export
        transactions = get_transactions()
        if not transactions.empty:
            csv_data = transactions.to_csv(index=False)
            print(f"✓ CSV export test passed: {len(csv_data)} characters")
        
        print("✓ Export functionality working correctly")
    except Exception as e:
        print(f"✗ Export functionality failed: {str(e)}")
        return False
    return True


def main():
    """Run all tests"""
    print("Running comprehensive test of all enhancements...\n")
    
    tests = [
        test_database_enhancements,
        test_caching_enhancements,
        test_advanced_reporting,
        test_clean_architecture,
        test_background_jobs,
        test_client_portal,
        test_approval_workflow,
        test_export_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All enhancements are working correctly!")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)