# backend/app/models/class_group.py

from sqlalchemy import Column, Integer, String, Boolean, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from enum import Enum as PyEnum
from typing import Optional
from app.models.associations import class_mandatory_subjects


class Grade(str, PyEnum):
    """Niveaux scolaires."""
    GRADE_6 = "6"
    GRADE_7 = "7"
    GRADE_8 = "8"
    GRADE_9 = "9"
    GRADE_10 = "10"
    GRADE_11 = "11"
    GRADE_12 = "12"


class ClassType(str, PyEnum):
    """Types de classes."""
    REGULAR = "regular"
    ADVANCED = "advanced"
    SPECIAL_NEEDS = "special_needs"


class ClassGroup(Base):
    """Modèle pour les groupes/classes."""
    __tablename__ = "class_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    
    # Champs renommés en anglais
    name = Column(String(255), nullable=False)  # Ancien: nom
    grade_name = Column(String(50), nullable=False)  # Ancien: niveau
    student_count = Column(Integer, nullable=False)  # Ancien: effectif
    
    # Type et description
    class_type = Column(Enum(ClassType), default=ClassType.REGULAR)
    description = Column(String(500))
    academic_year = Column(String(20))
    
    # Préférences horaires (JSON)
    preferred_schedules = Column(JSON)  # Ancien: horaires_preferes
    
    # Paramètres de genre
    is_boys_only = Column(Boolean, default=False)
    is_girls_only = Column(Boolean, default=False)
    is_mixed = Column(Boolean, default=True)
    
    # Langue principale
    primary_language = Column(String(2), default="he")  # he ou fr
    
    # Relations
    homeroom_teacher_id = Column(Integer, ForeignKey("teachers.id"))
    homeroom_teacher = relationship("Teacher", back_populates="homeroom_classes")
    
    # Matières obligatoires
    mandatory_subjects = relationship(
        "Subject",
        secondary=class_mandatory_subjects,
        back_populates="mandatory_for_classes"
    )
    
    # Requirements
    subject_requirements = relationship(
        "ClassSubjectRequirement", 
        back_populates="class_group",
        cascade="all, delete-orphan"
    )
    
    # Entrées d'emploi du temps
    schedule_entries = relationship(
        "ScheduleEntry", 
        back_populates="class_group"
    )
    
    # Actif/Inactif
    is_active = Column(Boolean, default=True)
    
    @property
    def grade_enum(self) -> Optional[Grade]:
        """Retourne le niveau comme enum."""
        try:
            return Grade(self.grade_name)
        except ValueError:
            return None
    
    @property
    def total_required_hours(self) -> int:
        """Calcule le total d'heures requises par semaine."""
        return sum(req.hours_per_week for req in self.subject_requirements)
    
    def __repr__(self):
        return f"<ClassGroup {self.code}: {self.name} ({self.student_count} students)>"