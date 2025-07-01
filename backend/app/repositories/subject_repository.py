"""
Subject repository with specialized queries.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.repositories.base import BaseRepository
from app.models.subject import Subject, SubjectType
from app.models.teacher import Teacher
from app.core.exceptions import DatabaseException


class SubjectRepository(BaseRepository[Subject]):
    """Repository for Subject entities with specialized queries."""
    
    def __init__(self, db: Session):
        super().__init__(Subject, db)
    
    def get_by_code(self, code: str) -> Optional[Subject]:
        """Get subject by code."""
        return self.get_by_field("code", code.upper())
    
    def get_active_subjects(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "name_he"
    ) -> List[Subject]:
        """Get all active subjects."""
        return self.get_by_filters(
            filters={"is_active": True},
            skip=skip,
            limit=limit,
            order_by=order_by
        )
    
    def get_subjects_by_type(self, subject_type: SubjectType) -> List[Subject]:
        """Get subjects by type."""
        return self.get_by_filters({
            "is_active": True,
            "subject_type": subject_type
        })
    
    def get_subjects_requiring_lab(self) -> List[Subject]:
        """Get subjects that require lab facilities."""
        return self.get_by_filters({
            "is_active": True,
            "requires_lab": True
        })
    
    def get_subjects_requiring_special_room(self) -> List[Subject]:
        """Get subjects that require special room."""
        return self.get_by_filters({
            "is_active": True,
            "requires_special_room": True
        })
    
    def get_religious_subjects(self) -> List[Subject]:
        """Get religious subjects."""
        return self.get_by_filters({
            "is_active": True,
            "is_religious": True
        })
    
    def get_subjects_requiring_gender_separation(self) -> List[Subject]:
        """Get subjects requiring gender separation."""
        return self.get_by_filters({
            "is_active": True,
            "requires_gender_separation": True
        })
    
    def get_subjects_with_teachers(self, skip: int = 0, limit: int = 100) -> List[Subject]:
        """Get subjects with their teachers loaded."""
        try:
            return (
                self.db.query(Subject)
                .options(joinedload(Subject.teachers))
                .filter(Subject.is_active == True)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            raise DatabaseException("get_subjects_with_teachers", e)
    
    def search_subjects(
        self, 
        search_term: str, 
        language: str = "he",
        skip: int = 0, 
        limit: int = 100
    ) -> List[Subject]:
        """Search subjects by name or code."""
        if not search_term:
            return self.get_active_subjects(skip, limit)
        
        search_pattern = f"%{search_term.lower()}%"
        
        try:
            query = self.db.query(Subject).filter(Subject.is_active == True)
            
            if language == "fr":
                query = query.filter(
                    or_(
                        func.lower(Subject.name_fr).like(search_pattern),
                        func.lower(Subject.code).like(search_pattern),
                        func.lower(Subject.abbreviation).like(search_pattern)
                    )
                )
            else:
                query = query.filter(
                    or_(
                        func.lower(Subject.name_he).like(search_pattern),
                        func.lower(Subject.code).like(search_pattern),
                        func.lower(Subject.abbreviation).like(search_pattern)
                    )
                )
            
            return query.order_by(Subject.name_he).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException("search_subjects", e)
    
    def get_subjects_by_teacher(self, teacher_id: int) -> List[Subject]:
        """Get all subjects that a teacher can teach."""
        try:
            return (
                self.db.query(Subject)
                .join(Subject.teachers)
                .filter(Teacher.id == teacher_id)
                .filter(Subject.is_active == True)
                .all()
            )
        except Exception as e:
            raise DatabaseException("get_subjects_by_teacher", e)
    
    def get_subjects_by_max_hours_per_day(self, max_hours: int) -> List[Subject]:
        """Get subjects with specific max hours per day constraint."""
        return self.get_by_filters({
            "is_active": True,
            "max_hours_per_day": max_hours
        })
    
    def get_subjects_requiring_consecutive_hours(self) -> List[Subject]:
        """Get subjects that require consecutive hours."""
        return self.get_by_filters({
            "is_active": True,
            "requires_consecutive_hours": True
        })
    
    def get_subjects_summary(self) -> Dict[str, Any]:
        """Get summary statistics for subjects."""
        try:
            total_subjects = self.count({"is_active": True})
            
            # Count by subject types
            subject_types = (
                self.db.query(Subject.subject_type, func.count(Subject.id))
                .filter(Subject.is_active == True)
                .group_by(Subject.subject_type)
                .all()
            )
            
            # Count special requirements
            lab_subjects = self.count({
                "is_active": True,
                "requires_lab": True
            })
            
            religious_subjects = self.count({
                "is_active": True,
                "is_religious": True
            })
            
            gender_separation_subjects = self.count({
                "is_active": True,
                "requires_gender_separation": True
            })
            
            # Count subjects with teachers
            subjects_with_teachers = (
                self.db.query(func.count(Subject.id.distinct()))
                .join(Subject.teachers)
                .filter(Subject.is_active == True)
                .scalar()
            )
            
            return {
                "total_active_subjects": total_subjects,
                "subject_types": dict(subject_types),
                "special_requirements": {
                    "requires_lab": lab_subjects,
                    "is_religious": religious_subjects,
                    "requires_gender_separation": gender_separation_subjects
                },
                "subjects_with_teachers": subjects_with_teachers,
                "subjects_without_teachers": total_subjects - subjects_with_teachers
            }
        except Exception as e:
            raise DatabaseException("get_subjects_summary", e)
    
    def assign_teachers_to_subject(self, subject_id: int, teacher_ids: List[int]) -> Subject:
        """Assign teachers to a subject."""
        try:
            subject = self.get_by_id_or_raise(subject_id)
            
            # Get teacher objects
            teachers = (
                self.db.query(Teacher)
                .filter(Teacher.id.in_(teacher_ids))
                .all()
            )
            
            # Clear existing teachers and assign new ones
            subject.teachers = teachers
            self.db.commit()
            self.db.refresh(subject)
            
            return subject
        except Exception as e:
            self.db.rollback()
            raise DatabaseException("assign_teachers_to_subject", e)
    
    def remove_teacher_from_subject(self, subject_id: int, teacher_id: int) -> Subject:
        """Remove a teacher from a subject."""
        try:
            subject = self.get_by_id_or_raise(subject_id)
            
            # Remove teacher from subject's teachers
            subject.teachers = [t for t in subject.teachers if t.id != teacher_id]
            self.db.commit()
            self.db.refresh(subject)
            
            return subject
        except Exception as e:
            self.db.rollback()
            raise DatabaseException("remove_teacher_from_subject", e) 