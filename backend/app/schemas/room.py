"""
Room schemas for API validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
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


class RoomBase(BaseModel):
    """Base room schema."""
    code: str = Field(..., min_length=1, max_length=20)  # e.g., "A101", "LAB-1"
    name: str
    room_type: RoomType = RoomType.REGULAR_CLASSROOM
    capacity: int = Field(..., ge=1, le=200)
    building: Optional[str] = None
    floor: Optional[int] = None
    has_projector: bool = False
    has_computers: bool = False
    has_lab_equipment: bool = False
    has_air_conditioning: bool = True
    is_accessible: bool = True
    is_active: bool = True
    suitable_for_prayer: bool = False
    gender_restricted: Optional[str] = Field(None, pattern="^(boys|girls)$")


class RoomCreate(RoomBase):
    """Schema for room creation."""
    pass


class RoomUpdate(BaseModel):
    """Schema for room update."""
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = None
    room_type: Optional[RoomType] = None
    capacity: Optional[int] = Field(None, ge=1, le=200)
    building: Optional[str] = None
    floor: Optional[int] = None
    has_projector: Optional[bool] = None
    has_computers: Optional[bool] = None
    has_lab_equipment: Optional[bool] = None
    has_air_conditioning: Optional[bool] = None
    is_accessible: Optional[bool] = None
    is_active: Optional[bool] = None
    suitable_for_prayer: Optional[bool] = None
    gender_restricted: Optional[str] = Field(None, pattern="^(boys|girls)$")


class RoomInDB(RoomBase):
    """Schema for room in database."""
    id: int
    
    class Config:
        from_attributes = True


class Room(RoomInDB):
    """Schema for room response."""
    unavailabilities: List["RoomUnavailability"] = []


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


# Rebuild models to handle forward references
Room.model_rebuild() 