"""
Teacher model for managing teaching staff.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Date, Text
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import re

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
    code = Column(String(50), unique=True, index=True, nullable=False)  # Unique teacher code
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
    
    # Working hours constraints
    max_hours_per_week = Column(Integer, default=30)
    max_hours_per_day = Column(Integer, default=8)
    prefers_consecutive_hours = Column(Boolean, default=True)
    
    # Employment details (added from migration)
    hire_date = Column(Date, nullable=True)
    contract_type = Column(String(50), nullable=True)  # 'full_time', 'part_time', 'substitute'
    notes = Column(Text, nullable=True)
    
    # Language preferences (for bilingual schools)
    primary_language = Column(String(2), default="he")  # 'he' or 'fr'
    can_teach_in_french = Column(Boolean, default=False)
    can_teach_in_hebrew = Column(Boolean, default=True)
    
    # Status and timestamps
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    subjects = relationship("Subject", secondary=teacher_subjects, back_populates="teachers")
    availabilities = relationship("TeacherAvailability", back_populates="teacher", cascade="all, delete-orphan")
    preferences = relationship("TeacherPreference", back_populates="teacher", cascade="all, delete-orphan")
    homeroom_classes = relationship("ClassGroup", foreign_keys="ClassGroup.homeroom_teacher_id")
    
    # Validations
    @validates('email')
    def validate_email(self, key, value):
        if value and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValueError("Invalid email format")
        return value
    
    @validates('max_hours_per_week')
    def validate_max_hours_per_week(self, key, value):
        if value is not None and (value < 1 or value > 60):
            raise ValueError("Max hours per week must be between 1 and 60")
        return value
    
    @validates('max_hours_per_day')
    def validate_max_hours_per_day(self, key, value):
        if value is not None and (value < 1 or value > 12):
            raise ValueError("Max hours per day must be between 1 and 12")
        return value
    
    @validates('code')
    def validate_code(self, key, value):
        if not value or len(value.strip()) == 0:
            raise ValueError("Teacher code cannot be empty")
        return value.strip().upper()
    
    # Properties
    @property
    def full_name(self):
        """Get teacher's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self):
        """Get formatted display name with code."""
        return f"{self.code} - {self.full_name}"
    
    @property
    def is_bilingual(self):
        """Check if teacher can teach in both languages."""
        return self.can_teach_in_french and self.can_teach_in_hebrew
    
    @property
    def subject_codes(self):
        """Get list of subject codes this teacher can teach."""
        return [subject.code for subject in self.subjects]
    
    def __repr__(self):
        return f"<Teacher(id={self.id}, code='{self.code}', name='{self.full_name}', active={self.is_active})>" 