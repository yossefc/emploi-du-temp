"""
Base service with common business logic operations.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from abc import ABC, abstractmethod

from app.repositories.base import BaseRepository, ModelType
from app.core.exceptions import (
    NotFoundException, 
    ValidationException, 
    BusinessRuleException,
    DuplicateException
)


ServiceModelType = TypeVar("ServiceModelType", bound=ModelType)


class BaseService(Generic[ServiceModelType], ABC):
    """Base service class with common business logic operations."""
    
    def __init__(self, repository: BaseRepository[ServiceModelType]):
        """
        Initialize service.
        
        Args:
            repository: Repository instance for data access
        """
        self.repository = repository
    
    @abstractmethod
    def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data for creating a new entity.
        
        Args:
            data: Raw input data
            
        Returns:
            Validated and processed data
            
        Raises:
            ValidationException: If validation fails
        """
        pass
    
    @abstractmethod
    def validate_update_data(self, id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data for updating an entity.
        
        Args:
            id: Entity ID
            data: Raw input data
            
        Returns:
            Validated and processed data
            
        Raises:
            ValidationException: If validation fails
        """
        pass
    
    def get_by_id(self, id: Any) -> Optional[ServiceModelType]:
        """Get entity by ID."""
        return self.repository.get_by_id(id)
    
    def get_by_id_or_raise(self, id: Any) -> ServiceModelType:
        """Get entity by ID or raise NotFoundException."""
        return self.repository.get_by_id_or_raise(id)
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[ServiceModelType]:
        """Get entity by a specific field."""
        return self.repository.get_by_field(field_name, value)
    
    def get_by_field_or_raise(self, field_name: str, value: Any) -> ServiceModelType:
        """Get entity by field or raise NotFoundException."""
        return self.repository.get_by_field_or_raise(field_name, value)
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None,
        desc_order: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ServiceModelType]:
        """Get all entities with pagination, ordering, and filtering."""
        if filters:
            return self.repository.get_by_filters(
                filters=filters,
                skip=skip,
                limit=limit,
                order_by=order_by,
                desc_order=desc_order
            )
        else:
            return self.repository.get_all(
                skip=skip,
                limit=limit,
                order_by=order_by,
                desc_order=desc_order
            )
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filters."""
        return self.repository.count(filters)
    
    def create(self, data: Dict[str, Any]) -> ServiceModelType:
        """
        Create new entity with validation.
        
        Args:
            data: Input data
            
        Returns:
            Created entity
            
        Raises:
            ValidationException: If validation fails
            DuplicateException: If entity already exists
            BusinessRuleException: If business rules are violated
        """
        # Validate input data
        validated_data = self.validate_create_data(data)
        
        # Check business rules before creation
        self._validate_business_rules_create(validated_data)
        
        # Create entity
        return self.repository.create(validated_data)
    
    def update(self, id: Any, data: Dict[str, Any]) -> ServiceModelType:
        """
        Update entity with validation.
        
        Args:
            id: Entity ID
            data: Update data
            
        Returns:
            Updated entity
            
        Raises:
            NotFoundException: If entity not found
            ValidationException: If validation fails
            BusinessRuleException: If business rules are violated
        """
        # Validate input data
        validated_data = self.validate_update_data(id, data)
        
        # Check business rules before update
        self._validate_business_rules_update(id, validated_data)
        
        # Update entity
        return self.repository.update(id, validated_data)
    
    def delete(self, id: Any) -> bool:
        """
        Delete entity with business rule validation.
        
        Args:
            id: Entity ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundException: If entity not found
            BusinessRuleException: If deletion violates business rules
        """
        # Check if entity exists
        entity = self.repository.get_by_id_or_raise(id)
        
        # Check business rules before deletion
        self._validate_business_rules_delete(entity)
        
        # Delete entity
        return self.repository.delete(id)
    
    def exists(self, id: Any) -> bool:
        """Check if entity exists by ID."""
        return self.repository.exists(id)
    
    def exists_by_field(self, field_name: str, value: Any) -> bool:
        """Check if entity exists by field."""
        return self.repository.exists_by_field(field_name, value)
    
    def _validate_business_rules_create(self, data: Dict[str, Any]) -> None:
        """
        Validate business rules for entity creation.
        Override in subclasses to add specific business rules.
        
        Args:
            data: Validated data for creation
            
        Raises:
            BusinessRuleException: If business rules are violated
        """
        pass
    
    def _validate_business_rules_update(self, id: Any, data: Dict[str, Any]) -> None:
        """
        Validate business rules for entity update.
        Override in subclasses to add specific business rules.
        
        Args:
            id: Entity ID
            data: Validated data for update
            
        Raises:
            BusinessRuleException: If business rules are violated
        """
        pass
    
    def _validate_business_rules_delete(self, entity: ServiceModelType) -> None:
        """
        Validate business rules for entity deletion.
        Override in subclasses to add specific business rules.
        
        Args:
            entity: Entity to be deleted
            
        Raises:
            BusinessRuleException: If business rules are violated
        """
        pass
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """
        Validate that required fields are present and not empty.
        
        Args:
            data: Input data
            required_fields: List of required field names
            
        Raises:
            ValidationException: If required fields are missing
        """
        missing_fields = []
        empty_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            elif data[field] is None or (isinstance(data[field], str) and data[field].strip() == ""):
                empty_fields.append(field)
        
        if missing_fields or empty_fields:
            error_msg = ""
            if missing_fields:
                error_msg += f"Missing required fields: {', '.join(missing_fields)}"
            if empty_fields:
                if error_msg:
                    error_msg += ". "
                error_msg += f"Empty required fields: {', '.join(empty_fields)}"
            
            raise ValidationException(error_msg)
    
    def _validate_field_length(self, data: Dict[str, Any], field_limits: Dict[str, int]) -> None:
        """
        Validate field length constraints.
        
        Args:
            data: Input data
            field_limits: Dict mapping field names to max lengths
            
        Raises:
            ValidationException: If field length constraints are violated
        """
        errors = {}
        
        for field, max_length in field_limits.items():
            if field in data and data[field] is not None:
                if isinstance(data[field], str) and len(data[field]) > max_length:
                    errors[field] = f"Field '{field}' exceeds maximum length of {max_length} characters"
        
        if errors:
            raise ValidationException(
                "Field length validation failed",
                validation_errors=errors
            ) 