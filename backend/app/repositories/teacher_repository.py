"""
Teacher repository with specialized queries.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from datetime import date, timedelta

from app.repositories.base import BaseRepository
from app.models.teacher import Teacher
from app.models.subject import Subject
from app.models.constraint import TeacherAvailability, DayOfWeek
from app.core.exceptions import DatabaseException


class TeacherRepository(BaseRepository[Teacher]):
    """Repository for Teacher entities with specialized queries."""
    
    def __init__(self, db: Session):
        super().__init__(Teacher, db)
    
    def get_by_code(self, code: str) -> Optional[Teacher]:
        """Get teacher by code."""
        return self.get_by_field("code", code.upper())
    
    def get_by_email(self, email: str) -> Optional[Teacher]:
        """Get teacher by email."""
        return self.get_by_field("email", email.lower())
    
    def get_active_teachers(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "last_name"
    ) -> List[Teacher]:
        """Get all active teachers."""
        return self.get_by_filters(
            filters={"is_active": True},
            skip=skip,
            limit=limit,
            order_by=order_by
        )
    
    def get_teachers_by_subject(self, subject_id: int) -> List[Teacher]:
        """Get all teachers who can teach a specific subject."""
        try:
            return (
                self.db.query(Teacher)
                .join(Teacher.subjects)
                .filter(Subject.id == subject_id)
                .filter(Teacher.is_active == True)
                .all()
            )
        except Exception as e:
            raise DatabaseException("get_teachers_by_subject", e)
    
    def get_teachers_by_language(self, language: str) -> List[Teacher]:
        """Get teachers who can teach in a specific language."""
        filters = {"is_active": True}
        
        if language.lower() == "he":
            filters["can_teach_in_hebrew"] = True
        elif language.lower() == "fr":
            filters["can_teach_in_french"] = True
        else:
            # Return empty list for unsupported languages
            return []
        
        return self.get_by_filters(filters)
    
    def get_bilingual_teachers(self) -> List[Teacher]:
        """Get teachers who can teach in both languages."""
        return self.get_by_filters({
            "is_active": True,
            "can_teach_in_hebrew": True,
            "can_teach_in_french": True
        })
    
    def get_teachers_with_subjects(self, skip: int = 0, limit: int = 100) -> List[Teacher]:
        """Get teachers with their subjects loaded."""
        try:
            return (
                self.db.query(Teacher)
                .options(joinedload(Teacher.subjects))
                .filter(Teacher.is_active == True)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            raise DatabaseException("get_teachers_with_subjects", e)
    
    def get_teachers_with_availability(
        self, 
        day_of_week: Optional[DayOfWeek] = None
    ) -> List[Teacher]:
        """Get teachers with their availability information."""
        try:
            query = (
                self.db.query(Teacher)
                .options(joinedload(Teacher.availabilities))
                .filter(Teacher.is_active == True)
            )
            
            if day_of_week is not None:
                query = query.join(Teacher.availabilities).filter(
                    TeacherAvailability.day_of_week == day_of_week,
                    TeacherAvailability.is_available == True
                )
            
            return query.all()
        except Exception as e:
            raise DatabaseException("get_teachers_with_availability", e)
    
    def search_teachers(
        self, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Teacher]:
        """Search teachers by name, code, or email."""
        if not search_term:
            return self.get_active_teachers(skip, limit)
        
        search_pattern = f"%{search_term.lower()}%"
        
        try:
            return (
                self.db.query(Teacher)
                .filter(
                    and_(
                        Teacher.is_active == True,
                        or_(
                            func.lower(Teacher.first_name).like(search_pattern),
                            func.lower(Teacher.last_name).like(search_pattern),
                            func.lower(Teacher.code).like(search_pattern),
                            func.lower(Teacher.email).like(search_pattern)
                        )
                    )
                )
                .order_by(Teacher.last_name, Teacher.first_name)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            raise DatabaseException("search_teachers", e)
    
    def get_teachers_by_workload_range(
        self, 
        min_hours: int, 
        max_hours: int
    ) -> List[Teacher]:
        """Get teachers within a specific workload range."""
        return self.get_by_filters({
            "is_active": True,
            "max_hours_per_week": list(range(min_hours, max_hours + 1))
        })
    
    def get_teachers_by_contract_type(self, contract_type: str) -> List[Teacher]:
        """Get teachers by contract type."""
        return self.get_by_filters({
            "is_active": True,
            "contract_type": contract_type
        })
    
    def get_recently_hired_teachers(self, days: int = 30) -> List[Teacher]:
        """Get teachers hired within the last N days."""
        try:
            cutoff_date = date.today() - timedelta(days=days)
            return (
                self.db.query(Teacher)
                .filter(
                    and_(
                        Teacher.is_active == True,
                        Teacher.hire_date >= cutoff_date
                    )
                )
                .order_by(Teacher.hire_date.desc())
                .all()
            )
        except Exception as e:
            raise DatabaseException("get_recently_hired_teachers", e)
    
    def get_teachers_availability_summary(self) -> Dict[str, Any]:
        """Get a summary of teachers' availability."""
        try:
            total_teachers = self.count({"is_active": True})
            
            # Count teachers by language capabilities
            hebrew_teachers = self.count({
                "is_active": True,
                "can_teach_in_hebrew": True
            })
            
            french_teachers = self.count({
                "is_active": True,
                "can_teach_in_french": True
            })
            
            bilingual_teachers = self.count({
                "is_active": True,
                "can_teach_in_hebrew": True,
                "can_teach_in_french": True
            })
            
            # Count by contract types
            contract_types = (
                self.db.query(Teacher.contract_type, func.count(Teacher.id))
                .filter(Teacher.is_active == True)
                .group_by(Teacher.contract_type)
                .all()
            )
            
            return {
                "total_active_teachers": total_teachers,
                "language_capabilities": {
                    "hebrew": hebrew_teachers,
                    "french": french_teachers,
                    "bilingual": bilingual_teachers
                },
                "contract_types": dict(contract_types),
                "average_max_hours": self._get_average_max_hours()
            }
        except Exception as e:
            raise DatabaseException("get_teachers_availability_summary", e)
    
    def _get_average_max_hours(self) -> float:
        """Get average maximum hours per week for active teachers."""
        try:
            result = (
                self.db.query(func.avg(Teacher.max_hours_per_week))
                .filter(Teacher.is_active == True)
                .scalar()
            )
            return float(result) if result else 0.0
        except Exception as e:
            raise DatabaseException("get_average_max_hours", e)
    
    def assign_subjects_to_teacher(self, teacher_id: int, subject_ids: List[int]) -> Teacher:
        """Assign subjects to a teacher."""
        try:
            teacher = self.get_by_id_or_raise(teacher_id)
            
            # Get subject objects
            subjects = (
                self.db.query(Subject)
                .filter(Subject.id.in_(subject_ids))
                .all()
            )
            
            # Clear existing subjects and assign new ones
            teacher.subjects = subjects
            self.db.commit()
            self.db.refresh(teacher)
            
            return teacher
        except Exception as e:
            self.db.rollback()
            raise DatabaseException("assign_subjects_to_teacher", e)
    
    def remove_subject_from_teacher(self, teacher_id: int, subject_id: int) -> Teacher:
        """Remove a subject from a teacher."""
        try:
            teacher = self.get_by_id_or_raise(teacher_id)
            
            # Remove subject from teacher's subjects
            teacher.subjects = [s for s in teacher.subjects if s.id != subject_id]
            self.db.commit()
            self.db.refresh(teacher)
            
            return teacher
        except Exception as e:
            self.db.rollback()
            raise DatabaseException("remove_subject_from_teacher", e) 