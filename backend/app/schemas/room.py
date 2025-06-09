"""
Room schemas for API validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import time
from enum import Enum


class RoomType(str, Enum):
    """Room type enumeration."""
    REGULAR_CLASSROOM = "regular_classroom"
    SCIENCE_LAB = "science_lab"
    COMPUTER_LAB = "computer_lab"
    SPORTS_HALL = "sports_hall"
    ART_ROOM = "art_room"
    MUSIC_ROOM = "music_room"
    LIBRARY = "library"
    PRAYER_ROOM = "prayer_room"
    AUDITORIUM = "auditorium"
    CONFERENCE_ROOM = "conference_room"
    LABORATORY = "laboratory"


class RoomBase(BaseModel):
    """Base room schema with enhanced fields."""
    code: str = Field(..., min_length=1, max_length=20, description="Unique room code")
    nom: str = Field(..., min_length=1, max_length=255, description="Room name")
    capacite: int = Field(..., ge=1, le=200, description="Maximum capacity")
    type_salle: RoomType = Field(default=RoomType.REGULAR_CLASSROOM, description="Room type")
    
    # Location information
    building: Optional[str] = Field(None, max_length=100, description="Building name")
    floor: Optional[int] = Field(None, description="Floor number")
    location_details: Optional[str] = Field(None, description="Additional location details")
    
    # Equipment and features (JSON structure)
    equipements: Optional[Dict[str, Any]] = Field(None, description="Equipment and features")
    
    # Availability schedule (JSON structure)
    disponibilites: Optional[Dict[str, Any]] = Field(None, description="Available time slots")
    
    # Legacy compatibility fields
    name: Optional[str] = Field(None, description="Legacy name field")
    capacity: Optional[int] = Field(None, ge=1, le=200, description="Legacy capacity field")
    room_type: Optional[RoomType] = Field(None, description="Legacy room type field")
    
    # Legacy individual equipment flags
    has_projector: bool = False
    has_computers: bool = False
    has_lab_equipment: bool = False
    has_air_conditioning: bool = True
    is_accessible: bool = True
    
    # Status and restrictions
    is_active: bool = True
    is_bookable: bool = True
    requires_supervision: bool = False
    
    # Additional metadata
    description: Optional[str] = Field(None, description="Room description")
    maintenance_notes: Optional[str] = Field(None, description="Maintenance notes")
    last_maintenance: Optional[str] = Field(None, description="Last maintenance date")
    
    # Israeli-specific settings
    suitable_for_prayer: bool = False
    gender_restricted: Optional[str] = Field(None, pattern="^(boys|girls)$")

    @validator('code')
    def validate_code(cls, v):
        """Validate room code format."""
        if not v or not v.strip():
            raise ValueError('Room code cannot be empty')
        return v.strip().upper()
    
    @validator('capacite', 'capacity')
    def validate_capacity(cls, v):
        """Validate capacity is reasonable."""
        if v is not None and (v < 1 or v > 200):
            raise ValueError('Capacity must be between 1 and 200')
        return v
    
    @validator('equipements')
    def validate_equipements(cls, v):
        """Validate equipment structure."""
        if v is not None and not isinstance(v, dict):
            raise ValueError('Equipment must be a dictionary')
        return v
    
    @validator('disponibilites')
    def validate_disponibilites(cls, v):
        """Validate availability structure."""
        if v is not None and not isinstance(v, dict):
            raise ValueError('Availability must be a dictionary')
        return v


class RoomCreate(RoomBase):
    """Schema for room creation."""
    pass


class RoomUpdate(BaseModel):
    """Schema for room update."""
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    nom: Optional[str] = Field(None, min_length=1, max_length=255)
    capacite: Optional[int] = Field(None, ge=1, le=200)
    type_salle: Optional[RoomType] = None
    building: Optional[str] = Field(None, max_length=100)
    floor: Optional[int] = None
    location_details: Optional[str] = None
    equipements: Optional[Dict[str, Any]] = None
    disponibilites: Optional[Dict[str, Any]] = None
    has_projector: Optional[bool] = None
    has_computers: Optional[bool] = None
    has_lab_equipment: Optional[bool] = None
    has_air_conditioning: Optional[bool] = None
    is_accessible: Optional[bool] = None
    is_active: Optional[bool] = None
    is_bookable: Optional[bool] = None
    requires_supervision: Optional[bool] = None
    description: Optional[str] = None
    maintenance_notes: Optional[str] = None
    last_maintenance: Optional[str] = None
    suitable_for_prayer: Optional[bool] = None
    gender_restricted: Optional[str] = Field(None, pattern="^(boys|girls)$")

    @validator('code')
    def validate_code(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Room code cannot be empty')
            return v.strip().upper()
        return v


class RoomInDB(RoomBase):
    """Schema for room in database."""
    id: int
    
    class Config:
        from_attributes = True


class Room(RoomInDB):
    """Schema for room response."""
    pass


class RoomBasic(BaseModel):
    """Basic room info for nested responses."""
    id: int
    code: str
    nom: str
    capacite: int
    type_salle: RoomType
    building: Optional[str] = None
    floor: Optional[int] = None
    
    class Config:
        from_attributes = True


class RoomAvailabilityQuery(BaseModel):
    """Schema for querying room availability."""
    day_of_week: int = Field(..., ge=0, le=5, description="Day of week (0=Sunday, 5=Friday)")
    start_time: str = Field(..., description="Start time (HH:MM format)")
    end_time: str = Field(..., description="End time (HH:MM format)")
    min_capacity: Optional[int] = Field(None, ge=1, description="Minimum required capacity")
    required_equipment: Optional[List[str]] = Field(None, description="Required equipment list")
    room_type: Optional[RoomType] = Field(None, description="Required room type")

    @validator('start_time', 'end_time')
    def validate_time_format(cls, v):
        """Validate time format HH:MM."""
        try:
            time_parts = v.split(':')
            if len(time_parts) != 2:
                raise ValueError('Time must be in HH:MM format')
            hours, minutes = int(time_parts[0]), int(time_parts[1])
            if not (0 <= hours <= 23) or not (0 <= minutes <= 59):
                raise ValueError('Invalid time values')
            return v
        except (ValueError, AttributeError):
            raise ValueError('Time must be in HH:MM format')


class RoomConflictCheck(BaseModel):
    """Schema for checking room booking conflicts."""
    room_id: int
    day_of_week: int = Field(..., ge=0, le=5)
    start_time: str
    end_time: str
    exclude_booking_id: Optional[int] = Field(None, description="Booking ID to exclude from conflict check")


# Legacy schemas for compatibility
class RoomUnavailabilityBase(BaseModel):
    """Base schema for room unavailability."""
    room_id: int
    day_of_week: int = Field(..., ge=0, le=5)  # 0-5 (Sunday-Friday)
    start_time: time
    end_time: time
    reason: Optional[str] = None


class RoomUnavailabilityCreate(RoomUnavailabilityBase):
    """Schema for creating room unavailability."""
    pass


class RoomUnavailability(RoomUnavailabilityBase):
    """Schema for room unavailability response."""
    id: int
    
    class Config:
        from_attributes = True 