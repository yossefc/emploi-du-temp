"""Subject — matière (bilingue FR/HE)."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base_mixin import TimestampMixin


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_subject_school_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    code = Column(String(30), nullable=False)              # ex: "MATH", "TANAKH"
    name_fr = Column(String(200), nullable=False)
    name_he = Column(String(200), nullable=False)
    abbreviation = Column(String(15), nullable=True)
    color_hex = Column(String(7), nullable=True)           # ex: "#3B82F6"

    # Type de salle requis (libre, école définit ses types) — ex: "lab", "gym", "computer"
    # Le solveur cherchera des Room avec room_type matching.
    required_room_type = Column(String(50), nullable=True)

    # Informationnel uniquement — aucune logique métier ne dépend de ce flag.
    # Permet à l'UI de regrouper / colorer. Si une école veut traiter ses matières
    # religieuses différemment, elle pose des contraintes explicites.
    is_religious = Column(Boolean, default=False, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    school = relationship("School", back_populates="subjects")
    groups = relationship("Group", back_populates="subject", cascade="all, delete-orphan")
