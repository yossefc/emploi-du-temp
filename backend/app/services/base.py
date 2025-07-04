"""Base service class for common operations."""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict, TypeVar, Generic

from app.repositories.base import BaseRepository
from app.core.exceptions import ValidationException

T = TypeVar('T')


class BaseService(Generic[T], ABC):
    """Base service providing common CRUD operations."""
    
    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository
    
    @abstractmethod
    def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data before creation."""
        pass
    
    @abstractmethod
    def validate_update_data(self, id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data before update."""
        pass
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """Get entity by ID."""
        return self.repository.get_by_id(id)
    
    def get_by_id_or_raise(self, id: Any) -> T:
        """Get entity by ID or raise exception."""
        return self.repository.get_by_id_or_raise(id)
    
    def get_by_field(self, field: str, value: Any) -> Optional[T]:
        """Get entity by field value."""
        return self.repository.get_by_field(field, value)
    
    def get_all(self, skip: int = 0, limit: int = 100, 
                filters: Optional[Dict[str, Any]] = None,
                order_by: Optional[str] = None, 
                desc_order: bool = False) -> List[T]:
        """Get all entities with optional filters."""
        if filters:
            return self.repository.get_by_filters(
                filters=filters, skip=skip, limit=limit, 
                order_by=order_by, desc_order=desc_order
            )
        return self.repository.get_all(
            skip=skip, limit=limit, order_by=order_by, desc_order=desc_order
        )
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filters."""
        return self.repository.count(filters)
    
    def create(self, data: Dict[str, Any]) -> T:
        """Create new entity."""
        validated_data = self.validate_create_data(data)
        return self.repository.create(validated_data)
    
    def update(self, id: Any, data: Dict[str, Any]) -> T:
        """Update entity."""
        validated_data = self.validate_update_data(id, data)
        return self.repository.update(id, validated_data)
    
    def delete(self, id: Any) -> bool:
        """Delete entity."""
        self.repository.get_by_id_or_raise(id)  # Ensure it exists
        return self.repository.delete(id)
    
    def exists(self, id: Any) -> bool:
        """Check if entity exists."""
        return self.repository.exists(id)
    
    def exists_by_field(self, field: str, value: Any) -> bool:
        """Check if entity exists by field value."""
        return self.repository.exists_by_field(field, value)
