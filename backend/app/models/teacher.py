"""Teacher — enseignant rattaché à une école."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base_mixin import TimestampMixin
from app.models.associations import teacher_qualified_subjects


class Teacher(Base, TimestampMixin):
    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_teacher_school_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)

    # Plafonds (informatifs, peuvent être surchargés par Constraint)
    max_hours_per_week = Column(Integer, nullable=True)
    max_hours_per_day = Column(Integer, nullable=True)

    # Langues d'enseignement supportées : JSON liste, ex ["fr", "he"]
    languages = Column(JSON, default=lambda: ["fr", "he"], nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    school = relationship("School", back_populates="teachers")
    user = relationship("User", back_populates="teacher", uselist=False)
    qualified_subjects = relationship(
        "Subject", secondary=teacher_qualified_subjects, backref="qualified_teachers"
    )
    groups = relationship("Group", secondary="group_teachers", back_populates="teachers")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
