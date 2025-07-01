"""
Room model for managing classrooms and facilities.
"""

from sqlalchemy import Column, Integer, String, Boolean, Enum, JSON, Text, DateTime
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
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
    
    # Basic information - unified English names
    name = Column(String(255), nullable=False)  # Room name
    capacity = Column(Integer, nullable=False)  # Maximum capacity
    room_type = Column(Enum(RoomType), nullable=False, default=RoomType.REGULAR_CLASSROOM)
    
    # Location information
    building = Column(String(100), nullable=True)  # Building name or number
    floor = Column(Integer, nullable=True)
    location_details = Column(Text, nullable=True)  # Additional location info
    
    # Equipment and features (JSON format)
    equipment = Column(JSON, nullable=True)  # Equipment list with details
    
    # Availability schedule (JSON format)
    availability_schedule = Column(JSON, nullable=True)  # Available time slots
    
    # Individual equipment flags
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
    last_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    schedule_entries = relationship("ScheduleEntry", back_populates="room")
    unavailabilities = relationship("RoomUnavailability", back_populates="room", cascade="all, delete-orphan")
    
    # Validations
    @validates('capacity')
    def validate_capacity(self, key, value):
        if value is not None and value < 1:
            raise ValueError("Room capacity must be at least 1")
        return value
    
    @validates('code')
    def validate_code(self, key, value):
        if not value or len(value.strip()) == 0:
            raise ValueError("Room code cannot be empty")
        return value.strip().upper()
    
    @validates('gender_restricted')
    def validate_gender_restricted(self, key, value):
        if value and value not in ['boys', 'girls']:
            raise ValueError("Gender restriction must be 'boys' or 'girls'")
        return value
    
    @validates('floor')
    def validate_floor(self, key, value):
        if value is not None and value < -5:  # Allow basement levels
            raise ValueError("Floor cannot be below -5")
        return value
    
    # Properties
    @property
    def display_name(self):
        """Get formatted display name."""
        return f"{self.code} - {self.name}"
    
    @property
    def location_full(self):
        """Get full location description."""
        parts = []
        if self.building:
            parts.append(f"Building {self.building}")
        if self.floor is not None:
            parts.append(f"Floor {self.floor}")
        if self.location_details:
            parts.append(self.location_details)
        return ", ".join(parts) if parts else "Location not specified"
    
    @property
    def is_lab(self):
        """Check if room is a laboratory."""
        return self.room_type in [RoomType.SCIENCE_LAB, RoomType.COMPUTER_LAB, RoomType.LABORATORY]
    
    @property
    def is_gender_restricted(self):
        """Check if room has gender restrictions."""
        return self.gender_restricted is not None
    
    @property
    def equipment_list(self):
        """Get list of available equipment."""
        equipment = []
        if self.has_projector:
            equipment.append("Projector")
        if self.has_computers:
            equipment.append("Computers")
        if self.has_lab_equipment:
            equipment.append("Lab Equipment")
        if self.has_air_conditioning:
            equipment.append("Air Conditioning")
        return equipment
    
    @property
    def suitability_tags(self):
        """Get list of suitability tags."""
        tags = []
        if self.is_accessible:
            tags.append("Wheelchair Accessible")
        if self.suitable_for_prayer:
            tags.append("Prayer Suitable")
        if self.requires_supervision:
            tags.append("Requires Supervision")
        return tags
    
    def __repr__(self):
        return f"<Room(id={self.id}, code='{self.code}', name='{self.name}', type='{self.room_type.value}', capacity={self.capacity})>" 