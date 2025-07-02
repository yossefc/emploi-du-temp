"""
Teacher Service - Business logic for teacher management.

This service handles all teacher-related business operations including:
- CRUD operations
- Subject assignments
- Workload calculations
- Availability management
- Schedule analysis
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.models.teacher import Teacher
from app.models.subject import Subject
from app.models.schedule import ScheduleEntry
from app.schemas.teacher import (
    TeacherCreate,
    TeacherUpdate,
    TeacherWorkload,
    TeacherAvailable,
    Teacher as TeacherSchema
)
from app.repositories.teacher_repository import TeacherRepository
from app.core.exceptions import (
    NotFoundException,
    DuplicateException,
    ValidationException,
    BusinessRuleException
)
from app.services.base import BaseService


class TeacherService(BaseService[Teacher]):
    """Service for teacher business logic."""
    
    def __init__(self, teacher_repository: TeacherRepository):
        """Initialize the service with repository."""
        super().__init__(teacher_repository)
        self.teacher_repo = teacher_repository
    
    def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data before creation."""
        # Basic validation - could be expanded
        if 'code' not in data or not data['code']:
            raise ValidationException("Teacher code is required")
        if 'first_name' not in data or not data['first_name']:
            raise ValidationException("First name is required")
        if 'last_name' not in data or not data['last_name']:
            raise ValidationException("Last name is required")
        return data
    
    def validate_update_data(self, id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data before update."""
        # Basic validation - could be expanded
        return data
    
    def create_teacher(self, teacher_data: TeacherCreate) -> Teacher:
        """
        Create a new teacher with validation.
        
        Args:
            teacher_data: Teacher creation data
            
        Returns:
            Created teacher
            
        Raises:
            DuplicateException: If teacher code or email already exists
            ValidationException: If data is invalid
        """
        # Check for duplicate code
        if self.teacher_repo.get_by_code(teacher_data.code):
            raise DuplicateException(f"Teacher with code '{teacher_data.code}' already exists")
        
        # Check for duplicate email
        if teacher_data.email and self.teacher_repo.get_by_email(teacher_data.email):
            raise DuplicateException(f"Teacher with email '{teacher_data.email}' already exists")
        
        # Validate business rules
        self._validate_teacher_data(teacher_data)
        
        # Create teacher
        teacher = self.teacher_repo.create(teacher_data)
        return teacher
    
    def update_teacher(self, teacher_id: int, teacher_data: TeacherUpdate) -> Teacher:
        """
        Update teacher with validation.
        
        Args:
            teacher_id: Teacher ID
            teacher_data: Updated teacher data
            
        Returns:
            Updated teacher
            
        Raises:
            NotFoundException: If teacher not found
            DuplicateException: If new code/email conflicts
            ValidationException: If data is invalid
        """
        teacher = self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise NotFoundException(f"Teacher with ID {teacher_id} not found")
        
        # Check for duplicate code (if changed)
        if teacher_data.code and teacher_data.code != teacher.code:
            if self.teacher_repo.get_by_code(teacher_data.code):
                raise DuplicateException(f"Teacher with code '{teacher_data.code}' already exists")
        
        # Check for duplicate email (if changed)
        if teacher_data.email and teacher_data.email != teacher.email:
            if self.teacher_repo.get_by_email(teacher_data.email):
                raise DuplicateException(f"Teacher with email '{teacher_data.email}' already exists")
        
        # Validate business rules
        self._validate_teacher_data(teacher_data, is_update=True)
        
        # Update teacher
        updated_teacher = self.teacher_repo.update(teacher_id, teacher_data)
        return updated_teacher
    
    def delete_teacher(self, teacher_id: int, force: bool = False) -> bool:
        """
        Delete teacher with business rule validation.
        
        Args:
            teacher_id: Teacher ID
            force: Force delete even with active schedules
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundException: If teacher not found
            BusinessRuleException: If teacher has active schedules and force=False
        """
        teacher = self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise NotFoundException(f"Teacher with ID {teacher_id} not found")
        
        # Check for active schedules
        if not force:
            active_schedules = self._count_active_schedules(teacher_id)
            if active_schedules > 0:
                raise BusinessRuleException(
                    f"Cannot delete teacher with {active_schedules} active schedule(s). Use force=True to override."
                )
        
        return self.teacher_repo.delete(teacher_id)
    
    def get_teacher_by_id(self, teacher_id: int) -> Optional[Teacher]:
        """Get teacher by ID with all related data."""
        return self.teacher_repo.get_by_id(teacher_id)
    
    def get_teachers_with_filters(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Teacher]:
        """
        Get teachers with filters and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            filters: Filter criteria
            
        Returns:
            List of teachers
        """
        return self.teacher_repo.get_with_filters(skip=skip, limit=limit, filters=filters or {})
    
    def assign_subjects(self, teacher_id: int, subject_ids: List[int]) -> Dict[str, Any]:
        """
        Assign subjects to a teacher.
        
        Args:
            teacher_id: Teacher ID
            subject_ids: List of subject IDs to assign
            
        Returns:
            Assignment result
            
        Raises:
            NotFoundException: If teacher or subject not found
            ValidationException: If subjects are invalid for teacher
        """
        teacher = self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise NotFoundException(f"Teacher with ID {teacher_id} not found")
        
        # Validate subjects exist
        for subject_id in subject_ids:
            subject = self.teacher_repo.db.query(Subject).filter(Subject.id == subject_id).first()
            if not subject:
                raise NotFoundException(f"Subject with ID {subject_id} not found")
        
        # Validate subject assignment rules
        self._validate_subject_assignment(teacher, subject_ids)
        
        # Assign subjects
        result = self.teacher_repo.assign_subjects(teacher_id, subject_ids)
        
        return {
            "teacher_id": teacher_id,
            "assigned_subjects": subject_ids,
            "total_subjects": len(subject_ids),
            "success": True
        }
    
    def get_teacher_workload(
        self, 
        teacher_id: int, 
        academic_year: Optional[str] = None,
        semester: Optional[int] = None
    ) -> TeacherWorkload:
        """
        Calculate teacher's workload and schedule analysis.
        
        Args:
            teacher_id: Teacher ID
            academic_year: Academic year filter
            semester: Semester filter
            
        Returns:
            Teacher workload analysis
            
        Raises:
            NotFoundException: If teacher not found
        """
        teacher = self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise NotFoundException(f"Teacher with ID {teacher_id} not found")
        
        # Get schedule entries for the teacher
        query = self.teacher_repo.db.query(ScheduleEntry).filter(
            ScheduleEntry.teacher_id == teacher_id
        )
        
        if academic_year:
            # Filter by academic year if provided
            pass  # Implement academic year filtering
        
        if semester:
            # Filter by semester if provided
            pass  # Implement semester filtering
        
        schedule_entries = query.all()
        
        # Calculate workload metrics
        total_hours = len(schedule_entries)
        hours_by_day = {}
        hours_by_subject = {}
        
        for entry in schedule_entries:
            # Count hours by day
            day = entry.day_of_week
            hours_by_day[day] = hours_by_day.get(day, 0) + 1
            
            # Count hours by subject
            subject_id = entry.subject_id
            hours_by_subject[subject_id] = hours_by_subject.get(subject_id, 0) + 1
        
        # Calculate utilization
        max_hours = teacher.max_hours_per_week or 30
        utilization_percentage = (total_hours / max_hours) * 100 if max_hours > 0 else 0
        
        return TeacherWorkload(
            teacher_id=teacher_id,
            total_hours_assigned=total_hours,
            max_hours_per_week=max_hours,
            utilization_percentage=utilization_percentage,
            hours_by_day=hours_by_day,
            hours_by_subject=hours_by_subject,
            academic_year=academic_year or "current",
            semester=semester or "all"
        )
    
    def get_available_teachers(self, filters: Dict[str, Any]) -> List[TeacherAvailable]:
        """
        Get teachers available for specific criteria.
        
        Args:
            filters: Filter criteria (day_of_week, period, subject_id, etc.)
            
        Returns:
            List of available teachers
        """
        # Get all active teachers
        teachers = self.teacher_repo.get_with_filters(filters={"is_active": True})
        
        available_teachers = []
        
        for teacher in teachers:
            # Check availability based on filters
            is_available = self._check_teacher_availability(teacher, filters)
            
            if is_available:
                available_teachers.append(TeacherAvailable(
                    teacher_id=teacher.id,
                    code=teacher.code,
                    full_name=teacher.full_name,
                    subjects=[s.code for s in teacher.subjects],
                    max_hours_per_week=teacher.max_hours_per_week,
                    current_hours=self._get_current_hours(teacher.id),
                    available_languages=[
                        lang for lang in ["he", "fr"] 
                        if getattr(teacher, f"can_teach_in_{lang.replace('he', 'hebrew').replace('fr', 'french')}", False)
                    ]
                ))
        
        return available_teachers
    
    def _validate_teacher_data(self, teacher_data, is_update: bool = False):
        """Validate teacher data according to business rules."""
        # Validate max hours
        if hasattr(teacher_data, 'max_hours_per_week') and teacher_data.max_hours_per_week:
            if teacher_data.max_hours_per_week < 1 or teacher_data.max_hours_per_week > 60:
                raise ValidationException("Max hours per week must be between 1 and 60")
        
        if hasattr(teacher_data, 'max_hours_per_day') and teacher_data.max_hours_per_day:
            if teacher_data.max_hours_per_day < 1 or teacher_data.max_hours_per_day > 12:
                raise ValidationException("Max hours per day must be between 1 and 12")
        
        # Validate language settings
        if hasattr(teacher_data, 'can_teach_in_hebrew') and hasattr(teacher_data, 'can_teach_in_french'):
            if not teacher_data.can_teach_in_hebrew and not teacher_data.can_teach_in_french:
                raise ValidationException("Teacher must be able to teach in at least one language")
    
    def _validate_subject_assignment(self, teacher: Teacher, subject_ids: List[int]):
        """Validate subject assignment business rules."""
        # Example business rule: A teacher can't teach more than 5 subjects
        if len(subject_ids) > 5:
            raise ValidationException("A teacher cannot be assigned to more than 5 subjects")
        
        # Example: Check if teacher language capabilities match subject requirements
        subjects = self.teacher_repo.db.query(Subject).filter(Subject.id.in_(subject_ids)).all()
        for subject in subjects:
            # Add subject-specific validation if needed
            pass
    
    def _count_active_schedules(self, teacher_id: int) -> int:
        """Count active schedule entries for a teacher."""
        return self.teacher_repo.db.query(ScheduleEntry).filter(
            ScheduleEntry.teacher_id == teacher_id
        ).count()
    
    def _check_teacher_availability(self, teacher: Teacher, filters: Dict[str, Any]) -> bool:
        """Check if teacher is available based on filters."""
        # Check subject compatibility
        if "subject_id" in filters:
            subject_ids = [s.id for s in teacher.subjects]
            if filters["subject_id"] not in subject_ids:
                return False
        
        # Check language requirements
        if "language" in filters:
            lang = filters["language"]
            if lang == "he" and not teacher.can_teach_in_hebrew:
                return False
            if lang == "fr" and not teacher.can_teach_in_french:
                return False
        
        # Check time slot availability (simplified)
        if "day_of_week" in filters and "period" in filters:
            # Check if teacher has schedule conflict
            existing_entry = self.teacher_repo.db.query(ScheduleEntry).filter(
                ScheduleEntry.teacher_id == teacher.id,
                ScheduleEntry.day_of_week == filters["day_of_week"],
                ScheduleEntry.period == filters["period"]
            ).first()
            
            if existing_entry:
                return False
        
        return True
    
    def _get_current_hours(self, teacher_id: int) -> int:
        """Get current assigned hours for a teacher."""
        return self.teacher_repo.db.query(ScheduleEntry).filter(
            ScheduleEntry.teacher_id == teacher_id
        ).count()
