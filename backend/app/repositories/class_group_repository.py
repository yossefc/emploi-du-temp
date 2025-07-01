"""
ClassGroup repository with specialized queries.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.repositories.base import BaseRepository
from app.models.class_group import ClassGroup, ClassType
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.core.exceptions import DatabaseException


class ClassGroupRepository(BaseRepository[ClassGroup]):
    """Repository for ClassGroup entities with specialized queries."""
    
    def __init__(self, db: Session):
        super().__init__(ClassGroup, db)
    
    def get_by_code(self, code: str) -> Optional[ClassGroup]:
        """Get class group by code."""
        return self.get_by_field("code", code.upper())
    
    def get_active_class_groups(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "grade_level"
    ) -> List[ClassGroup]:
        """Get all active class groups."""
        return self.get_by_filters(
            filters={"is_active": True},
            skip=skip,
            limit=limit,
            order_by=order_by
        )
    
    def get_by_grade_level(self, grade_level: str) -> List[ClassGroup]:
        """Get class groups by grade level."""
        return self.get_by_filters({
            "is_active": True,
            "grade_level": grade_level
        })
    
    def get_by_teacher(self, teacher_id: int) -> List[ClassGroup]:
        """Get class groups for a specific homeroom teacher."""
        return self.get_by_filters({
            "is_active": True,
            "homeroom_teacher_id": teacher_id
        })
    
    def get_by_student_count_range(
        self, 
        min_count: int, 
        max_count: int
    ) -> List[ClassGroup]:
        """Get class groups by student count range."""
        try:
            return self.db.query(self.model).filter(
                and_(
                    self.model.is_active == True,
                    self.model.student_count >= min_count,
                    self.model.student_count <= max_count
                )
            ).all()
        except Exception as e:
            raise DatabaseException("get_by_student_count_range", e)
    
    def get_by_class_type(self, class_type: ClassType) -> List[ClassGroup]:
        """Get class groups by type."""
        return self.get_by_filters({
            "is_active": True,
            "class_type": class_type
        })
    
    def get_mixed_classes(self) -> List[ClassGroup]:
        """Get mixed gender classes."""
        return self.get_by_filters({
            "is_active": True,
            "is_mixed": True
        })
    
    def get_boys_only_classes(self) -> List[ClassGroup]:
        """Get boys-only classes."""
        return self.get_by_filters({
            "is_active": True,
            "is_boys_only": True
        })
    
    def get_girls_only_classes(self) -> List[ClassGroup]:
        """Get girls-only classes."""
        return self.get_by_filters({
            "is_active": True,
            "is_girls_only": True
        })
    
    def get_by_language(self, language: str) -> List[ClassGroup]:
        """Get class groups by primary language."""
        return self.get_by_filters({
            "is_active": True,
            "primary_language": language
        })
    
    def get_by_academic_year(self, academic_year: str) -> List[ClassGroup]:
        """Get class groups by academic year."""
        return self.get_by_filters({
            "is_active": True,
            "academic_year": academic_year
        })
    
    def search_class_groups(
        self, 
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClassGroup]:
        """Search class groups by name or code."""
        try:
            search_pattern = f"%{search_term}%"
            return self.db.query(self.model).filter(
                and_(
                    self.model.is_active == True,
                    or_(
                        self.model.name.ilike(search_pattern),
                        self.model.code.ilike(search_pattern)
                    )
                )
            ).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException("search_class_groups", e)
    
    def get_classes_with_subjects(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClassGroup]:
        """Get class groups with their assigned subjects."""
        try:
            return self.db.query(self.model).options(
                joinedload(self.model.subjects)
            ).filter(
                self.model.is_active == True
            ).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException("get_classes_with_subjects", e)
    
    def get_classes_with_homeroom_teachers(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClassGroup]:
        """Get class groups with their homeroom teachers."""
        try:
            return self.db.query(self.model).options(
                joinedload(self.model.homeroom_teacher)
            ).filter(
                self.model.is_active == True
            ).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException("get_classes_with_homeroom_teachers", e)
    
    def get_class_groups_needing_homeroom_teacher(self) -> List[ClassGroup]:
        """Get active class groups without homeroom teacher."""
        return self.get_by_filters({
            "is_active": True,
            "homeroom_teacher_id": None
        })
    
    def count_by_grade_level(self) -> Dict[str, int]:
        """Get count of classes by grade level."""
        try:
            result = self.db.query(
                self.model.grade_level,
                func.count(self.model.id).label('count')
            ).filter(
                self.model.is_active == True
            ).group_by(self.model.grade_level).all()
            
            return {grade: count for grade, count in result}
        except Exception as e:
            raise DatabaseException("count_by_grade_level", e)
    
    def get_total_students_by_grade(self) -> Dict[str, int]:
        """Get total students by grade level."""
        try:
            result = self.db.query(
                self.model.grade_level,
                func.sum(self.model.student_count).label('total_students')
            ).filter(
                self.model.is_active == True
            ).group_by(self.model.grade_level).all()
            
            return {grade: total or 0 for grade, total in result}
        except Exception as e:
            raise DatabaseException("get_total_students_by_grade", e)
    
    def get_classes_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of class groups."""
        try:
            # Basic counts
            total_classes = self.count({"is_active": True})
            total_students = self.db.query(
                func.sum(self.model.student_count)
            ).filter(self.model.is_active == True).scalar() or 0
            
            # By type
            type_counts = {}
            for class_type in ClassType:
                count = self.count({
                    "is_active": True,
                    "class_type": class_type
                })
                type_counts[class_type.value] = count
            
            # By gender
            mixed_count = self.count({"is_active": True, "is_mixed": True})
            boys_only_count = self.count({"is_active": True, "is_boys_only": True})
            girls_only_count = self.count({"is_active": True, "is_girls_only": True})
            
            # Average class size
            avg_class_size = total_students / total_classes if total_classes > 0 else 0
            
            return {
                "total_classes": total_classes,
                "total_students": total_students,
                "average_class_size": round(avg_class_size, 1),
                "by_type": type_counts,
                "by_gender": {
                    "mixed": mixed_count,
                    "boys_only": boys_only_count,
                    "girls_only": girls_only_count
                },
                "by_grade": self.count_by_grade_level(),
                "students_by_grade": self.get_total_students_by_grade()
            }
        except Exception as e:
            raise DatabaseException("get_classes_summary", e) 