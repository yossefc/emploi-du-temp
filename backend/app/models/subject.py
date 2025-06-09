"""
Subject model for managing school subjects.
"""

from sqlalchemy import Column, Integer, String, Boolean, Enum, Text
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base
from app.models.teacher import teacher_subjects


class SubjectType(str, enum.Enum):
    """Subject type enumeration."""
    OBLIGATOIRE = "obligatoire"      # Mandatory subjects
    OPTIONNELLE = "optionnelle"      # Optional subjects
    SPECIALISEE = "specialisee"      # Specialized subjects
    ACADEMIC = "academic"            # Keep existing for compatibility
    SPORTS = "sports"
    ARTS = "arts"
    RELIGIOUS = "religious"
    LANGUAGE = "language"
    SCIENCE_LAB = "science_lab"


class Subject(Base):
    """Subject model with bilingual support."""
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    
    # Bilingual names (required)
    nom_fr = Column(String(255), nullable=False)    # French name
    nom_he = Column(String(255), nullable=False)    # Hebrew name
    
    # Legacy names for compatibility
    name_fr = Column(String(255), nullable=True)    
    name_he = Column(String(255), nullable=True)
    
    # New required fields
    niveau_requis = Column(String(50), nullable=False)     # Required level (e.g., "6ème", "5ème", etc.)
    heures_semaine = Column(Integer, nullable=False)       # Hours per week (1-40)
    type_matiere = Column(Enum(SubjectType), nullable=False, default=SubjectType.OBLIGATOIRE)
    
    # Bilingual descriptions
    description_fr = Column(Text, nullable=True)
    description_he = Column(Text, nullable=True)
    
    # Legacy compatibility fields
    subject_type = Column(Enum(SubjectType), default=SubjectType.ACADEMIC)
    
    # Requirements
    requires_lab = Column(Boolean, default=False)
    requires_special_room = Column(Boolean, default=False)
    requires_consecutive_hours = Column(Boolean, default=False)
    max_hours_per_day = Column(Integer, default=2)
    
    # Israeli-specific settings
    is_religious = Column(Boolean, default=False)
    requires_gender_separation = Column(Boolean, default=False)
    
    # Relationships
    teachers = relationship("Teacher", secondary=teacher_subjects, back_populates="subjects")
    class_requirements = relationship("ClassSubjectRequirement", back_populates="subject")
    
    # Many-to-many relationship with ClassGroups
    class_groups = relationship(
        "ClassGroup", 
        secondary="class_group_subjects", 
        back_populates="matieres_obligatoires",
        lazy="select"
    ) 