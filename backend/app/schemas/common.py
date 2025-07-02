"""
Common schemas for API validation.
"""

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(
        default=1, 
        ge=1, 
        description="Page number (1-based)",
        examples=[1, 2, 3]
    )
    size: int = Field(
        default=20, 
        ge=1, 
        le=100, 
        description="Number of items per page",
        examples=[10, 20, 50]
    )
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.size

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "page": 1,
                "size": 20
            }
        }


class PaginationResponse(BaseModel):
    """Schema for pagination metadata in responses."""
    page: int = Field(description="Current page number")
    size: int = Field(description="Items per page")
    total: int = Field(description="Total number of items")
    pages: int = Field(description="Total number of pages")
    has_prev: bool = Field(description="Whether there is a previous page")
    has_next: bool = Field(description="Whether there is a next page")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "page": 1,
                "size": 20,
                "total": 45,
                "pages": 3,
                "has_prev": False,
                "has_next": True
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: bool = Field(default=True, description="Indicates this is an error response")
    message: str = Field(description="Human-readable error message")
    error_code: Optional[str] = Field(
        default=None, 
        description="Machine-readable error code"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional error details"
    )
    field_errors: Optional[Dict[str, List[str]]] = Field(
        default=None, 
        description="Field-specific validation errors"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "examples": [
                {
                    "error": True,
                    "message": "Validation failed",
                    "error_code": "VALIDATION_ERROR",
                    "field_errors": {
                        "email": ["Invalid email format"],
                        "age": ["Must be greater than 0"]
                    }
                },
                {
                    "error": True,
                    "message": "Resource not found",
                    "error_code": "NOT_FOUND",
                    "details": {
                        "resource_type": "Teacher",
                        "resource_id": 123
                    }
                }
            ]
        }


class SuccessResponse(BaseModel):
    """Schema for success responses."""
    success: bool = Field(default=True, description="Indicates this is a success response")
    message: str = Field(description="Human-readable success message")
    data: Optional[Any] = Field(
        default=None, 
        description="Response data"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional response metadata"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "message": "Teacher created successfully",
                    "data": {
                        "id": 1,
                        "code": "T001",
                        "first_name": "John",
                        "last_name": "Doe"
                    }
                },
                {
                    "success": True,
                    "message": "Schedule generated successfully",
                    "metadata": {
                        "generation_time": 45.2,
                        "conflicts_resolved": 3
                    }
                }
            ]
        }


class PaginatedResponse(BaseModel):
    """Schema for paginated responses."""
    success: bool = Field(default=True, description="Indicates this is a success response")
    data: List[Any] = Field(description="List of items")
    pagination: PaginationResponse = Field(description="Pagination metadata")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"}
                ],
                "pagination": {
                    "page": 1,
                    "size": 20,
                    "total": 45,
                    "pages": 3,
                    "has_prev": False,
                    "has_next": True
                }
            }
        }


class HealthCheckResponse(BaseModel):
    """Schema for health check responses."""
    status: str = Field(description="Service health status")
    timestamp: str = Field(description="Health check timestamp")
    version: Optional[str] = Field(default=None, description="API version")
    dependencies: Optional[Dict[str, str]] = Field(
        default=None, 
        description="Status of external dependencies"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "version": "1.0.0",
                "dependencies": {
                    "database": "healthy",
                    "redis": "healthy"
                }
            }
        }


class BulkOperationRequest(BaseModel):
    """Schema for bulk operations."""
    operation: str = Field(description="Type of bulk operation")
    items: List[Dict[str, Any]] = Field(
        description="List of items to process",
        min_items=1,
        max_items=1000
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional operation options"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "operation": "create_teachers",
                "items": [
                    {"code": "T001", "first_name": "John", "last_name": "Doe"},
                    {"code": "T002", "first_name": "Jane", "last_name": "Smith"}
                ],
                "options": {
                    "skip_duplicates": True,
                    "validate_references": False
                }
            }
        }


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation responses."""
    success: bool = Field(description="Overall operation success")
    message: str = Field(description="Operation summary message")
    total_items: int = Field(description="Total number of items processed")
    successful_items: int = Field(description="Number of successfully processed items")
    failed_items: int = Field(description="Number of failed items")
    errors: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of errors for failed items"
    )
    results: Optional[List[Any]] = Field(
        default=None,
        description="Results for successful items"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Bulk operation completed",
                "total_items": 10,
                "successful_items": 8,
                "failed_items": 2,
                "errors": [
                    {"item_index": 3, "error": "Duplicate code"},
                    {"item_index": 7, "error": "Invalid email format"}
                ]
            }
        } 