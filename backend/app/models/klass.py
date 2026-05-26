"""Class (כיתה) — classe administrative (homeroom).

Fichier nommé klass.py car `class` est un mot réservé Python.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base_mixin import TimestampMixin


class Class(Base, TimestampMixin):
    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_class_school_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    grade_id = Column(Integer, ForeignKey("grades.id", ondelete="CASCADE"), nullable=False, index=True)

    code = Column(String(20), nullable=False)         # ex: "ז-1", "11A"
    name = Column(String(100), nullable=False)        # ex: "Septième 1"
    student_count = Column(Integer, default=0, nullable=False)

    homeroom_teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)

    school = relationship("School", back_populates="classes")
    grade = relationship("Grade", back_populates="classes")
    homeroom_teacher = relationship("Teacher", foreign_keys=[homeroom_teacher_id])
    groups = relationship("Group", secondary="group_source_classes", back_populates="source_classes")
