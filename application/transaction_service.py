"""
Transaction service for business logic related to transactions
"""
from typing import List, Optional
from domain.entities import Transaction
from infrastructure.repositories import TransactionRepository
from application.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository

    def create_transaction(self, transaction: Transaction) -> int:
        """Create a new transaction with validation"""
        # Validate transaction data
        self._validate_transaction(transaction)
        
        # Create transaction in repository
        transaction_id = self.transaction_repository.create(transaction)
        
        logger.info(f"Transaction created: {transaction_id} - {transaction.description}")
        
        # Invalidate related caches
        from infrastructure.cache import invalidate_transaction_cache
        invalidate_transaction_cache()
        
        return transaction_id

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Get a transaction by ID"""
        return self.transaction_repository.get_by_id(transaction_id)

    def get_transactions(self, page: int = 1, page_size: int = 50) -> List[Transaction]:
        """Get paginated transactions"""
        return self.transaction_repository.get_all(page, page_size)

    def update_transaction(self, transaction: Transaction) -> bool:
        """Update an existing transaction"""
        if not transaction.id:
            raise ValidationError("Transaction ID is required for update")
        
        self._validate_transaction(transaction)
        
        updated = self.transaction_repository.update(transaction)
        
        if updated:
            logger.info(f"Transaction updated: {transaction.id} - {transaction.description}")
            
            # Invalidate related caches
            from infrastructure.cache import invalidate_transaction_cache
            invalidate_transaction_cache()
        
        return updated

    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction"""
        deleted = self.transaction_repository.delete(transaction_id)
        
        if deleted:
            logger.info(f"Transaction deleted: {transaction_id}")
            
            # Invalidate related caches
            from infrastructure.cache import invalidate_transaction_cache
            invalidate_transaction_cache()
        
        return deleted

    def _validate_transaction(self, transaction: Transaction):
        """Validate transaction data"""
        errors = []
        
        if not transaction.description or not transaction.description.strip():
            errors.append("Description is required")
        
        if not transaction.category or not transaction.category.strip():
            errors.append("Category is required")
        
        if transaction.amount <= 0:
            errors.append("Amount must be greater than 0")
        
        if transaction.type not in ["Income", "Expense", "Salary", "Investment", "Loan"]:
            errors.append("Invalid transaction type")
        
        if errors:
            raise ValidationError(f"Transaction validation failed: {', '.join(errors)}")