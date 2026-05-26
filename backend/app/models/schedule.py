"""Schedule + ScheduleEntry — emploi du temps généré et ses entrées.

CHANGEMENT FONDAMENTAL vs ancienne version : ScheduleEntry référence un
`Group`, pas un `Class`. Cela permet de modéliser les barrettes (un Group
peut servir plusieurs Classes) et les sous-divisions (plusieurs Groups
parallèles pour la même Class).
"""

import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base_mixin import TimestampMixin


class ScheduleStatus(str, enum.Enum):
    DRAFT = "draft"            # brouillon, en cours de génération / édition
    ACTIVE = "active"          # version courante diffusée
    ARCHIVED = "archived"      # ancienne version conservée


class Schedule(Base, TimestampMixin):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=False)              # ex: "2026-2027 v1"
    status = Column(Enum(ScheduleStatus), nullable=False, default=ScheduleStatus.DRAFT)

    generated_at = Column(DateTime(timezone=True), nullable=True)
    generator_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Rapport des contraintes ignorées pour atteindre cette solution (JSON list)
    relaxed_constraints_report = Column(JSON, nullable=True)
    # Score qualité (combien de soft respectées, etc.)
    quality_score = Column(JSON, nullable=True)

    school = relationship("School", back_populates="schedules")
    entries = relationship("ScheduleEntry", back_populates="schedule", cascade="all, delete-orphan")
    generator_user = relationship("User", foreign_keys=[generator_user_id])


class ScheduleEntry(Base, TimestampMixin):
    __tablename__ = "schedule_entries"
    __table_args__ = (
        # Un Group ne peut pas être placé deux fois sur le même créneau d'un schedule
        UniqueConstraint("schedule_id", "group_id", "day_of_week", "slot_index",
                         name="uq_entry_schedule_group_day_slot"),
    )

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True, index=True)

    day_of_week = Column(Integer, nullable=False)           # 0-6
    slot_index = Column(Integer, nullable=False)

    schedule = relationship("Schedule", back_populates="entries")
    group = relationship("Group", back_populates="schedule_entries")
    room = relationship("Room", back_populates="schedule_entries")
