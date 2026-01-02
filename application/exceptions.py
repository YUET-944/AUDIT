"""
Custom exceptions for the application layer
"""


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


class BusinessRuleViolation(Exception):
    """Raised when a business rule is violated"""
    pass


class ResourceNotFound(Exception):
    """Raised when a requested resource is not found"""
    pass


class AccessDenied(Exception):
    """Raised when access to a resource is denied"""
    pass


class OperationFailed(Exception):
    """Raised when an operation fails"""
    pass