"""
Base repository with generic CRUD operations.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc

from app.db.base import Base
from app.core.exceptions import NotFoundException, DuplicateException, DatabaseException


# Define a proper base type for type annotations
class BaseModelType:
    """Base model type for better type annotations."""
    id: Any
    

ModelType = TypeVar("ModelType", bound=BaseModelType)


class BaseRepository(Generic[ModelType]):
    """Base repository class with generic CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db
    
    def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Get entity by ID."""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            raise DatabaseException("get_by_id", e)
    
    def get_by_id_or_raise(self, id: Any) -> ModelType:
        """Get entity by ID or raise NotFoundException."""
        entity = self.get_by_id(id)
        if not entity:
            raise NotFoundException(self.model.__name__, id)
        return entity
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """Get entity by a specific field."""
        try:
            return self.db.query(self.model).filter(
                getattr(self.model, field_name) == value
            ).first()
        except SQLAlchemyError as e:
            raise DatabaseException(f"get_by_{field_name}", e)
    
    def get_by_field_or_raise(self, field_name: str, value: Any) -> ModelType:
        """Get entity by field or raise NotFoundException."""
        entity = self.get_by_field(field_name, value)
        if not entity:
            raise NotFoundException(self.model.__name__, f"{field_name}={value}")
        return entity
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None,
        desc_order: bool = False
    ) -> List[ModelType]:
        """Get all entities with pagination and ordering."""
        try:
            query = self.db.query(self.model)
            
            if order_by and hasattr(self.model, order_by):
                order_field = getattr(self.model, order_by)
                if desc_order:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseException("get_all", e)
    
    def get_by_filters(
        self, 
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        desc_order: bool = False
    ) -> List[ModelType]:
        """Get entities by multiple filters."""
        try:
            query = self.db.query(self.model)
            
            # Apply filters
            for field_name, value in filters.items():
                if hasattr(self.model, field_name) and value is not None:
                    if isinstance(value, list):
                        # Handle IN queries
                        query = query.filter(getattr(self.model, field_name).in_(value))
                    elif isinstance(value, str) and value.startswith('%') and value.endswith('%'):
                        # Handle LIKE queries
                        query = query.filter(getattr(self.model, field_name).ilike(value))
                    else:
                        # Handle exact matches
                        query = query.filter(getattr(self.model, field_name) == value)
            
            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                order_field = getattr(self.model, order_by)
                if desc_order:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseException("get_by_filters", e)
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filters."""
        try:
            query = self.db.query(self.model)
            
            if filters:
                for field_name, value in filters.items():
                    if hasattr(self.model, field_name) and value is not None:
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, field_name).in_(value))
                        elif isinstance(value, str) and value.startswith('%') and value.endswith('%'):
                            query = query.filter(getattr(self.model, field_name).ilike(value))
                        else:
                            query = query.filter(getattr(self.model, field_name) == value)
            
            return query.count()
        except SQLAlchemyError as e:
            raise DatabaseException("count", e)
    
    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create new entity."""
        try:
            db_obj = self.model(**obj_in)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            self.db.rollback()
            # Try to determine which field caused the constraint violation
            error_msg = str(e.orig)
            if "UNIQUE constraint failed" in error_msg:
                # Extract field name from error message if possible
                field_name = "unknown"
                if hasattr(self.model, 'code') and 'code' in error_msg:
                    field_name = 'code'
                elif hasattr(self.model, 'email') and 'email' in error_msg:
                    field_name = 'email'
                
                raise DuplicateException(
                    self.model.__name__, 
                    field_name, 
                    obj_in.get(field_name, "unknown")
                )
            raise DatabaseException("create", e)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseException("create", e)
    
    def update(self, id: Any, obj_in: Dict[str, Any]) -> ModelType:
        """Update existing entity."""
        try:
            db_obj = self.get_by_id_or_raise(id)
            
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            self.db.rollback()
            error_msg = str(e.orig)
            if "UNIQUE constraint failed" in error_msg:
                field_name = "unknown"
                if hasattr(self.model, 'code') and 'code' in error_msg:
                    field_name = 'code'
                elif hasattr(self.model, 'email') and 'email' in error_msg:
                    field_name = 'email'
                
                raise DuplicateException(
                    self.model.__name__, 
                    field_name, 
                    obj_in.get(field_name, "unknown")
                )
            raise DatabaseException("update", e)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseException("update", e)
    
    def delete(self, id: Any) -> bool:
        """Delete entity by ID."""
        try:
            db_obj = self.get_by_id_or_raise(id)
            self.db.delete(db_obj)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseException("delete", e)
    
    def exists(self, id: Any) -> bool:
        """Check if entity exists by ID."""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first() is not None
        except SQLAlchemyError as e:
            raise DatabaseException("exists", e)
    
    def exists_by_field(self, field_name: str, value: Any) -> bool:
        """Check if entity exists by field."""
        try:
            return self.db.query(self.model).filter(
                getattr(self.model, field_name) == value
            ).first() is not None
        except SQLAlchemyError as e:
            raise DatabaseException(f"exists_by_{field_name}", e) 