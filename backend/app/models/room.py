"""
Room model for managing classrooms and facilities.
"""

from sqlalchemy import Column, Integer, String, Boolean, Enum, JSON, Text
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
    CONFERENCE_ROOM = "conference_room"
    LABORATORY = "laboratory"


class Room(Base):
    """Room model with enhanced equipment and availability management."""
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)  # e.g., "A101", "LAB-1"
    
    # Basic information
    nom = Column(String(255), nullable=False)  # Room name
    capacite = Column(Integer, nullable=False)  # Maximum capacity
    type_salle = Column(Enum(RoomType), nullable=False, default=RoomType.REGULAR_CLASSROOM)
    
    # Legacy fields for compatibility
    name = Column(String(255), nullable=True)
    capacity = Column(Integer, nullable=True)
    room_type = Column(Enum(RoomType), nullable=True)
    
    # Location information
    building = Column(String(100), nullable=True)  # Building name or number
    floor = Column(Integer, nullable=True)
    location_details = Column(Text, nullable=True)  # Additional location info
    
    # Equipment and features (JSON format)
    equipements = Column(JSON, nullable=True)  # Equipment list with details
    
    # Availability schedule (JSON format)
    disponibilites = Column(JSON, nullable=True)  # Available time slots
    
    # Legacy individual equipment flags (kept for compatibility)
    has_projector = Column(Boolean, default=False)
    has_computers = Column(Boolean, default=False)
    has_lab_equipment = Column(Boolean, default=False)
    has_air_conditioning = Column(Boolean, default=True)
    is_accessible = Column(Boolean, default=True)  # Wheelchair accessible
    
    # Status and restrictions
    is_active = Column(Boolean, default=True)
    is_bookable = Column(Boolean, default=True)  # Can be reserved
    requires_supervision = Column(Boolean, default=False)  # Needs teacher supervision
    
    # Israeli-specific settings
    suitable_for_prayer = Column(Boolean, default=False)
    gender_restricted = Column(String(10), nullable=True)  # null, 'boys', 'girls'
    
    # Additional metadata
    description = Column(Text, nullable=True)
    maintenance_notes = Column(Text, nullable=True)
    last_maintenance = Column(String(50), nullable=True)  # Date of last maintenance
    
    # Relationships
    schedules = relationship("ScheduleEntry", back_populates="room")
    unavailabilities = relationship("RoomUnavailability", back_populates="room", cascade="all, delete-orphan") 