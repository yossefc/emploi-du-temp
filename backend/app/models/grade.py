"""Grade (שכבה) — niveau scolaire / promotion."""

import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base_mixin import TimestampMixin


class GroupingPolicy(str, enum.Enum):
    """Politique de regroupement pour les matières non-barrette.

    - CLASS_CENTRIC : par défaut, les cours sont donnés à la Class entière (ex: primaire)
    - GROUP_CENTRIC : par défaut, les cours sont éclatés en Groups (ex: lycée)

    L'admin peut surcharger au niveau de chaque Subject.
    """
    CLASS_CENTRIC = "class_centric"
    GROUP_CENTRIC = "group_centric"


class Grade(Base, TimestampMixin):
    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_grade_school_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    code = Column(String(20), nullable=False)         # ex: "ז", "7", "11"
    name = Column(String(100), nullable=False)        # ex: "7ème année"
    order = Column(Integer, nullable=False)           # pour tri (1-12 ou autre)

    grouping_policy = Column(Enum(GroupingPolicy), default=GroupingPolicy.CLASS_CENTRIC, nullable=False)

    school = relationship("School", back_populates="grades")
    classes = relationship("Class", back_populates="grade", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="grade", cascade="all, delete-orphan")
    parallel_cohorts = relationship("ParallelCohort", back_populates="grade", cascade="all, delete-orphan")
