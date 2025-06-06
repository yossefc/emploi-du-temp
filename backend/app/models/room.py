"""
Room model for managing classrooms and facilities.
"""

from sqlalchemy import Column, Integer, String, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class RoomType(str, enum.Enum):
    """Room type enumeration."""
    REGULAR_CLASSROOM = "regular_classroom"
    SCIENCE_LAB = "science_lab"
    COMPUTER_LAB = "computer_lab"
    SPORTS_HALL = "sports_hall"
    ART_ROOM = "art_room"
    MUSIC_ROOM = "music_room"
    LIBRARY = "library"
    PRAYER_ROOM = "prayer_room"  # For religious schools
    AUDITORIUM = "auditorium"


class Room(Base):
    """Room model."""
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)  # e.g., "A101", "LAB-1"
    name = Column(String, nullable=False)
    room_type = Column(Enum(RoomType), default=RoomType.REGULAR_CLASSROOM)
    capacity = Column(Integer, nullable=False)
    building = Column(String)  # Building name or number
    floor = Column(Integer)
    
    # Features
    has_projector = Column(Boolean, default=False)
    has_computers = Column(Boolean, default=False)
    has_lab_equipment = Column(Boolean, default=False)
    has_air_conditioning = Column(Boolean, default=True)
    is_accessible = Column(Boolean, default=True)  # Wheelchair accessible
    
    # Availability
    is_active = Column(Boolean, default=True)
    
    # Israeli-specific settings
    suitable_for_prayer = Column(Boolean, default=False)
    gender_restricted = Column(String)  # null, 'boys', 'girls'
    
    # Relationships
    schedules = relationship("ScheduleEntry", back_populates="room")
    unavailabilities = relationship("RoomUnavailability", back_populates="room", cascade="all, delete-orphan") 