"""
Teacher model for managing teaching staff.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

# Association table for many-to-many relationship between teachers and subjects
teacher_subjects = Table(
    'teacher_subjects',
    Base.metadata,
    Column('teacher_id', Integer, ForeignKey('teachers.id')),
    Column('subject_id', Integer, ForeignKey('subjects.id'))
)


class Teacher(Base):
    """Teacher model."""
    __tablename__ = "teachers"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)  # Unique teacher code
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    max_hours_per_week = Column(Integer, default=30)
    max_hours_per_day = Column(Integer, default=8)
    prefers_consecutive_hours = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    # Language preferences (for bilingual schools)
    primary_language = Column(String(2), default="he")  # 'he' or 'fr'
    can_teach_in_french = Column(Boolean, default=False)
    can_teach_in_hebrew = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    subjects = relationship("Subject", secondary=teacher_subjects, back_populates="teachers")
    availabilities = relationship("TeacherAvailability", back_populates="teacher", cascade="all, delete-orphan")
    preferences = relationship("TeacherPreference", back_populates="teacher", cascade="all, delete-orphan")
    
    @property
    def full_name(self):
        """Get teacher's full name."""
        return f"{self.first_name} {self.last_name}" 