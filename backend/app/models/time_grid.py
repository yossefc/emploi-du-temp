"""TimeSlot — grille horaire configurable par école.

Chaque école définit librement ses jours actifs, ses créneaux par jour,
leurs heures de début/fin, et marque les pauses (non plaçables).
"""

from sqlalchemy import Column, Integer, String, Time, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base_mixin import TimestampMixin


class TimeSlot(Base, TimestampMixin):
    __tablename__ = "time_slots"
    __table_args__ = (
        UniqueConstraint("school_id", "day_of_week", "slot_index", name="uq_timeslot_school_day_index"),
    )

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # 0=Dimanche, 1=Lundi, ..., 6=Samedi (semaine israélienne : actifs typiquement 0-5)
    day_of_week = Column(Integer, nullable=False)
    slot_index = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    # Si True : créneau de pause (récréation, déjeuner) — aucun cours plaçable
    is_break = Column(Boolean, default=False, nullable=False)
    # Si False : ce créneau n'existe pas ce jour-là (ex: vendredi tronqué)
    is_active = Column(Boolean, default=True, nullable=False)

    # Libre : "Prière", "Récréation", "Déjeuner", etc.
    label = Column(String(100), nullable=True)

    school = relationship("School", back_populates="time_slots")
