"""Teacher service for teacher-specific operations."""

from typing import List, Dict, Any, Optional

from app.services.base import BaseService
from app.repositories.teacher_repository import TeacherRepository
from app.models.teacher import Teacher
from app.core.exceptions import ValidationException, DuplicateException


class TeacherService(BaseService[Teacher]):
    """Service for teacher operations."""
    
    def __init__(self, teacher_repository: TeacherRepository):
        super().__init__(teacher_repository)
        self.teacher_repo = teacher_repository
    
    def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate teacher data before creation."""
        required_fields = ["code", "first_name", "last_name", "email"]
        
        for field in required_fields:
            if not data.get(field):
                raise ValidationException(f"{field} is required", {"field": field})
        
        # Check if teacher code already exists
        existing_teacher = self.teacher_repo.get_by_code(data["code"])
        if existing_teacher:
            raise DuplicateException("Teacher", "code", data["code"])
        
        return data
    
    def validate_update_data(self, id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate teacher data before update."""
        # Ensure teacher exists
        teacher = self.teacher_repo.get_by_id_or_raise(id)
        
        # Prevent changing teacher code
        if "code" in data and data["code"] != teacher.code:
            raise ValidationException("Teacher code cannot be changed", {"field": "code"})
        
        return data
    
    def get_by_code(self, code: str) -> Optional[Teacher]:
        """Get teacher by code."""
        return self.teacher_repo.get_by_code(code)
    
    def search_teachers(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Teacher]:
        """Search teachers by name."""
        return self.teacher_repo.search_teachers(search_term, skip, limit)
    
    def get_active_teachers(self, skip: int = 0, limit: int = 100) -> List[Teacher]:
        """Get active teachers."""
        return self.teacher_repo.get_active_teachers(skip, limit)
