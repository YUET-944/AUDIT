"""
Dependency injection factory for the application
"""
import os
from infrastructure.repositories import SQLiteTransactionRepository, PostgreSQLTransactionRepository
from application.transaction_service import TransactionService
from application.client_portal_service import ClientPortalService
from application.approval_workflow_service import ApprovalWorkflowService


class DependencyFactory:
    """Factory for creating application dependencies"""
    
    @staticmethod
    def get_transaction_repository():
        """Get the appropriate transaction repository based on configuration"""
        db_type = os.getenv('DB_TYPE', 'sqlite').lower()
        
        if db_type == 'postgresql':
            return PostgreSQLTransactionRepository()
        else:
            return SQLiteTransactionRepository()
    
    @staticmethod
    def get_transaction_service():
        """Get a transaction service with the appropriate repository"""
        repository = DependencyFactory.get_transaction_repository()
        return TransactionService(repository)
    
    @staticmethod
    def get_client_portal_service():
        """Get a client portal service with the appropriate repository"""
        repository = DependencyFactory.get_transaction_repository()
        return ClientPortalService(repository)
    
    @staticmethod
    def get_approval_workflow_service():
        """Get an approval workflow service with the appropriate repository"""
        repository = DependencyFactory.get_transaction_repository()
        return ApprovalWorkflowService(repository)


# Global dependency factory instance
dependency_factory = DependencyFactory()