"""
Teacher service with business logic.
"""

from typing import Any, Dict, List, Optional
import re

from app.services.base import BaseService
from app.repositories.teacher_repository import TeacherRepository
from app.models.teacher import Teacher
from app.core.exceptions import (
    ValidationException, 
    BusinessRuleException, 
    NotFoundException,
    DuplicateException
)


class TeacherService(BaseService[Teacher]):
    """Service for Teacher business logic."""
    
    def __init__(self, teacher_repository: TeacherRepository):
        super().__init__(teacher_repository)
        self.teacher_repo = teacher_repository
    
    def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for creating a new teacher."""
        # Required fields
        required_fields = ["code", "first_name", "last_name", "email"]
        for field in required_fields:
            if not data.get(field):
                raise ValidationException(f"{field} is required", {"field": field})
        
        # Check for duplicate code
        if self.teacher_repo.get_by_code(data["code"]):
            raise DuplicateException("Teacher", "code", data["code"])
        
        return data
    
    def validate_update_data(self, id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for updating a teacher."""
        # Get existing teacher
        existing_teacher = self.get_by_id_or_raise(id)
        
        # Don't allow changing code
        if "code" in data and data["code"] != existing_teacher.code:
            raise ValidationException("Teacher code cannot be changed", {"field": "code"})
        
        return data
    
    def get_by_code(self, code: str) -> Optional[Teacher]:
        """Get teacher by code."""
        return self.teacher_repo.get_by_code(code)
    
    def search_teachers(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Teacher]:
        """Search teachers by name, code, or email."""
        return self.teacher_repo.search_teachers(search_term, skip, limit)
    
    def get_active_teachers(self, skip: int = 0, limit: int = 100) -> List[Teacher]:
        """Get all active teachers."""
        return self.teacher_repo.get_active_teachers(skip, limit)
    
    def get_teachers_by_subject(self, subject_id: int) -> List[Teacher]:
        """Get teachers who can teach a specific subject."""
        return self.teacher_repo.get_teachers_by_subject(subject_id)
    
    def get_bilingual_teachers(self) -> List[Teacher]:
        """Get teachers who can teach in both languages."""
        return self.teacher_repo.get_bilingual_teachers()
    
    def get_teacher_workload(self, teacher_id: int) -> Dict[str, Any]:
        """Get comprehensive workload information for a teacher."""
        teacher = self.get_by_id_or_raise(teacher_id)
        return self.teacher_repo.analyze_teacher_workload(teacher_id)
    
    def get_teachers_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all teachers."""
        return self.teacher_repo.get_teachers_summary()
    
    def activate_teacher(self, teacher_id: int) -> Teacher:
        """Activate a teacher."""
        return self.update(teacher_id, {"is_active": True})
    
    def deactivate_teacher(self, teacher_id: int, reason: Optional[str] = None) -> Teacher:
        """Deactivate a teacher with optional reason."""
        teacher = self.get_by_id_or_raise(teacher_id)
        
        # Check if teacher has any active assignments
        # This would be implemented based on your schedule model
        
        update_data = {"is_active": False}
        if reason:
            update_data["notes"] = f"{teacher.notes or ''}\nDeactivated: {reason}".strip()
        
        return self.update(teacher_id, update_data) 