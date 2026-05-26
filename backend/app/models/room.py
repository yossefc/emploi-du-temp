"""Room — salle rattachée à une école."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base_mixin import TimestampMixin


class Room(Base, TimestampMixin):
    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_room_school_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    code = Column(String(30), nullable=False)
    name = Column(String(200), nullable=False)
    capacity = Column(Integer, nullable=False, default=30)

    # Type libre, défini par l'école. Doit matcher Subject.required_room_type.
    room_type = Column(String(50), nullable=True, index=True)

    building = Column(String(100), nullable=True)
    floor = Column(Integer, nullable=True)
    equipment = Column(JSON, nullable=True)                # {"projector": true, "computers": 30}

    is_active = Column(Boolean, default=True, nullable=False)

    school = relationship("School", back_populates="rooms")
    schedule_entries = relationship("ScheduleEntry", back_populates="room")
