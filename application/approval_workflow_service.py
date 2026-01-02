"""
Approval workflow service for business logic related to transaction approvals
"""
from typing import List, Optional, Dict, Any
from domain.entities import User, Transaction
from infrastructure.repositories import TransactionRepository
from application.exceptions import ValidationError, AccessDenied, BusinessRuleViolation
import logging
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalWorkflowService:
    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository
        # In a real implementation, this would have access to an approval workflow repository
        self.approval_thresholds = {
            "admin": float('inf'),  # No limit for admins
            "finance_manager": 100000,  # 100,000 PKR
            "accountant": 50000,  # 50,000 PKR
            "employee": 10000  # 10,000 PKR
        }

    def requires_approval(self, transaction: Transaction, user_role: str) -> bool:
        """Check if a transaction requires approval based on amount and user role"""
        threshold = self.approval_thresholds.get(user_role, 0)
        return transaction.amount > threshold

    def create_approval_request(self, transaction_id: int, requestor_id: int, approver_ids: List[int]) -> Dict[str, Any]:
        """Create an approval request for a transaction"""
        # Get the transaction
        transaction = self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise ResourceNotFound(f"Transaction {transaction_id} not found")
        
        # In a real implementation, this would create an approval request in the database
        # For now, we'll simulate the approval request creation
        
        approval_request = {
            "id": f"approval_{transaction_id}_{requestor_id}_{datetime.now().timestamp()}",
            "transaction_id": transaction_id,
            "requestor_id": requestor_id,
            "approver_ids": approver_ids,
            "status": ApprovalStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),  # 7 days to approve
            "comments": []
        }
        
        logger.info(f"Approval request created for transaction {transaction_id} by user {requestor_id}")
        
        return approval_request

    def submit_for_approval(self, transaction: Transaction, user_id: int, user_role: str) -> Dict[str, Any]:
        """Submit a transaction for approval if required"""
        # Check if approval is required
        if not self.requires_approval(transaction, user_role):
            # No approval needed, just return the transaction
            return {
                "transaction_id": transaction.id,
                "requires_approval": False,
                "status": "processed",
                "message": "Transaction processed without approval"
            }
        
        # Approval is required
        # In a real implementation, this would create an approval workflow
        # For now, we'll just return an approval request object
        approver_ids = self._determine_approvers(transaction, user_role)
        
        approval_request = self.create_approval_request(
            transaction.id, 
            user_id, 
            approver_ids
        )
        
        return {
            "transaction_id": transaction.id,
            "requires_approval": True,
            "approval_request": approval_request,
            "status": "pending_approval",
            "message": f"Transaction submitted for approval. Requires approval from {len(approver_ids)} user(s)"
        }

    def _determine_approvers(self, transaction: Transaction, requestor_role: str) -> List[int]:
        """Determine which users need to approve this transaction"""
        # In a real implementation, this would query the database for approvers
        # based on transaction amount, type, department, etc.
        # For now, we'll return a fixed list of approver IDs as an example
        if transaction.amount > 500000:  # 500,000 PKR
            # High value transaction requires senior management approval
            return [1, 2]  # IDs of senior managers
        elif transaction.amount > 100000:  # 100,000 PKR
            # Mid value transaction requires manager approval
            return [3]  # ID of department manager
        else:
            # Lower value transaction requires accountant approval
            return [4]  # ID of accountant

    def approve_transaction(self, approval_request_id: str, approver_id: int, comment: Optional[str] = None) -> Dict[str, Any]:
        """Approve a transaction"""
        # In a real implementation, this would update the approval request in the database
        # For now, we'll simulate the approval process
        
        # Check if the approver is authorized to approve this request
        # (In a real implementation, this would verify against the approval request)
        
        result = {
            "approval_request_id": approval_request_id,
            "approver_id": approver_id,
            "status": ApprovalStatus.APPROVED.value,
            "approved_at": datetime.now().isoformat(),
            "comment": comment
        }
        
        logger.info(f"Transaction approval completed: {approval_request_id} by approver {approver_id}")
        
        return result

    def reject_transaction(self, approval_request_id: str, approver_id: int, reason: str) -> Dict[str, Any]:
        """Reject a transaction"""
        if not reason or not reason.strip():
            raise ValidationError("Reason for rejection is required")
        
        if len(reason) > 500:  # Limit reason length
            raise ValidationError("Rejection reason is too long (max 500 characters)")
        
        # In a real implementation, this would update the approval request in the database
        # For now, we'll simulate the rejection process
        
        result = {
            "approval_request_id": approval_request_id,
            "approver_id": approver_id,
            "status": ApprovalStatus.REJECTED.value,
            "rejected_at": datetime.now().isoformat(),
            "reason": reason
        }
        
        logger.info(f"Transaction rejection completed: {approval_request_id} by approver {approver_id}")
        
        return result

    def get_user_approvals(self, user_id: int) -> List[Dict[str, Any]]:
        """Get approval requests assigned to a user"""
        # In a real implementation, this would query the database for approval requests
        # assigned to the user
        # For now, we'll return an empty list as an example
        return []

    def can_approve_transaction(self, user_id: int, approval_request_id: str) -> bool:
        """Check if a user is authorized to approve a specific transaction"""
        # In a real implementation, this would check if the user is in the approver list
        # for the specific approval request
        # For now, we'll return True as an example
        return True