"""
Client portal service for business logic related to client access and collaboration
"""
from typing import List, Optional, Dict, Any
from domain.entities import User, Transaction
from infrastructure.repositories import TransactionRepository
from application.exceptions import ValidationError, AccessDenied, ResourceNotFound
import logging
import jwt
from datetime import datetime, timedelta
from infrastructure.cache import get_from_cache, set_to_cache, delete_from_cache

logger = logging.getLogger(__name__)


class ClientPortalService:
    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository

    def get_client_accessible_transactions(self, client_id: int, user_role: str) -> List[Transaction]:
        """Get transactions that a client is allowed to view"""
        if user_role not in ["client", "admin", "accountant"]:
            raise AccessDenied("User does not have permission to access client portal")
        
        # For a client role, only return transactions related to their projects/contracts
        # For this example, we'll return all transactions but in a real implementation
        # this would be filtered based on client relationships
        if user_role == "client":
            # In a real implementation, this would filter based on client_id
            # For now, return all transactions as an example
            transactions = self.transaction_repository.get_all(page=1, page_size=1000)
        else:
            # Admins and accountants can see all transactions
            transactions = self.transaction_repository.get_all(page=1, page_size=1000)
        
        return transactions

    def create_client_comment(self, transaction_id: int, user_id: int, comment: str) -> bool:
        """Add a comment to a transaction from a client perspective"""
        if not comment or not comment.strip():
            raise ValidationError("Comment cannot be empty")
        
        if len(comment) > 1000:  # Limit comment length
            raise ValidationError("Comment is too long (max 1000 characters)")
        
        # In a real implementation, this would add the comment to a comments table
        # For now, we'll just log the comment creation
        logger.info(f"Client {user_id} added comment to transaction {transaction_id}: {comment}")
        
        # Invalidate any related caches
        cache_key = f"transaction_comments_{transaction_id}"
        delete_from_cache(cache_key)
        
        return True

    def get_client_permissions(self, user_id: int, user_role: str) -> Dict[str, bool]:
        """Get the permissions available to a client user"""
        # Define permissions based on role
        permissions = {
            "view_transactions": user_role in ["client", "admin", "accountant"],
            "add_comments": user_role in ["client", "admin", "accountant"],
            "view_reports": user_role in ["client", "admin", "accountant"],
            "download_reports": user_role in ["admin", "accountant"],
            "edit_profile": user_role in ["client", "admin", "accountant"],
        }
        
        return permissions

    def validate_client_access(self, user_id: int, resource_type: str, resource_id: int) -> bool:
        """Validate if a client has access to a specific resource"""
        # In a real implementation, this would check the relationship between 
        # the client and the resource to determine access
        # For now, we'll return True for demonstration
        logger.info(f"Validating access for user {user_id} to {resource_type} {resource_id}")
        return True

    def generate_client_report(self, client_id: int, report_type: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a report for client access"""
        if report_type == "transaction_summary":
            # Get transactions for the client
            transactions = self.get_client_accessible_transactions(client_id, "client")
            
            # Calculate summary metrics
            total_income = sum(t.amount for t in transactions if t.type == "Income")
            total_expenses = sum(t.amount for t in transactions if t.type == "Expense")
            net_amount = total_income - total_expenses
            
            return {
                "report_type": "transaction_summary",
                "client_id": client_id,
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_amount": net_amount,
                "transaction_count": len(transactions),
                "generated_at": datetime.now().isoformat(),
                "filters": filters
            }
        
        elif report_type == "cash_flow":
            # This would call the advanced reporting module
            from advanced_reporting import AdvancedReporting
            reporter = AdvancedReporting()
            
            # Generate cash flow forecast
            forecast = reporter.cash_flow_forecasting(
                months_ahead=filters.get("months_ahead", 6)
            )
            
            return {
                "report_type": "cash_flow",
                "client_id": client_id,
                "forecast_data": forecast.to_dict('records') if hasattr(forecast, 'to_dict') else [],
                "generated_at": datetime.now().isoformat(),
                "filters": filters
            }
        
        else:
            raise ValidationError(f"Unknown report type: {report_type}")