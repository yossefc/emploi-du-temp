"""School — tenant racine de la plateforme."""

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base_mixin import TimestampMixin


class School(Base, TimestampMixin):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    timezone = Column(String(50), default="Asia/Jerusalem", nullable=False)
    default_language = Column(String(5), default="fr", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    time_slots = relationship("TimeSlot", back_populates="school", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="school", cascade="all, delete-orphan")
    classes = relationship("Class", back_populates="school", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="school", cascade="all, delete-orphan")
    teachers = relationship("Teacher", back_populates="school", cascade="all, delete-orphan")
    rooms = relationship("Room", back_populates="school", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="school", cascade="all, delete-orphan")
    parallel_cohorts = relationship("ParallelCohort", back_populates="school", cascade="all, delete-orphan")
    constraints = relationship("Constraint", back_populates="school", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="school", cascade="all, delete-orphan")
    users = relationship("User", back_populates="school")
