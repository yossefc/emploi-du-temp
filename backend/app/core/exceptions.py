"""
Custom exceptions for the application.
"""

from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """Base exception for all application exceptions."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)


class NotFoundException(BaseAppException):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self, 
        resource_type: str, 
        identifier: Any, 
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource_type} with identifier '{identifier}' not found"
        super().__init__(
            message=message,
            details=details,
            error_code="NOT_FOUND"
        )
        self.resource_type = resource_type
        self.identifier = identifier


class DuplicateException(BaseAppException):
    """Raised when attempting to create a resource that already exists."""
    
    def __init__(
        self, 
        resource_type: str, 
        field: str, 
        value: Any,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource_type} with {field} '{value}' already exists"
        super().__init__(
            message=message,
            details=details,
            error_code="DUPLICATE_RESOURCE"
        )
        self.resource_type = resource_type
        self.field = field
        self.value = value


class ValidationException(BaseAppException):
    """Raised when data validation fails."""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        validation_errors: Optional[Dict[str, str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            details=details,
            error_code="VALIDATION_ERROR"
        )
        self.field = field
        self.validation_errors = validation_errors or {}


class BusinessRuleException(BaseAppException):
    """Raised when a business rule is violated."""
    
    def __init__(
        self, 
        rule_name: str, 
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Business rule violation '{rule_name}': {message}",
            details=details,
            error_code="BUSINESS_RULE_VIOLATION"
        )
        self.rule_name = rule_name


class PermissionException(BaseAppException):
    """Raised when user lacks permission for an operation."""
    
    def __init__(
        self, 
        operation: str, 
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Permission denied for operation '{operation}'"
        if resource:
            message += f" on resource '{resource}'"
        
        super().__init__(
            message=message,
            details=details,
            error_code="PERMISSION_DENIED"
        )
        self.operation = operation
        self.resource = resource


class DatabaseException(BaseAppException):
    """Raised when database operations fail."""
    
    def __init__(
        self, 
        operation: str, 
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Database operation '{operation}' failed"
        if original_error:
            message += f": {str(original_error)}"
        
        super().__init__(
            message=message,
            details=details,
            error_code="DATABASE_ERROR"
        )
        self.operation = operation
        self.original_error = original_error


class ConflictException(BaseAppException):
    """Raised when there's a conflict in the current state."""
    
    def __init__(
        self, 
        resource_type: str, 
        conflict_reason: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Conflict with {resource_type}: {conflict_reason}"
        super().__init__(
            message=message,
            details=details,
            error_code="CONFLICT"
        )
        self.resource_type = resource_type
        self.conflict_reason = conflict_reason 