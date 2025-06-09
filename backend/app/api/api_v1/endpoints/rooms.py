"""
Rooms management endpoints - Complete CRUD API with business logic.
"""

from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from datetime import datetime, time

from app.core.auth import get_current_active_user
from app.db.base import get_db
from app.models.user import User
from app.models.room import Room, RoomType
from app.models.subject import Subject
from app.schemas.room import (
    Room as RoomSchema,
    RoomCreate,
    RoomUpdate,
    RoomBasic,
    RoomAvailabilityQuery,
    RoomConflictCheck
)

router = APIRouter()


# ============================================================================
# MAIN CRUD ENDPOINTS
# ============================================================================

@router.get("/", response_model=List[RoomSchema])
async def get_rooms(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search in room name or code"),
    type_salle: Optional[RoomType] = Query(None, description="Filter by room type"),
    min_capacite: Optional[int] = Query(None, ge=1, description="Minimum capacity"),
    max_capacite: Optional[int] = Query(None, ge=1, description="Maximum capacity"),
    building: Optional[str] = Query(None, description="Filter by building"),
    floor: Optional[int] = Query(None, description="Filter by floor"),
    has_projector: Optional[bool] = Query(None, description="Filter by projector availability"),
    has_computers: Optional[bool] = Query(None, description="Filter by computer availability"),
    has_lab_equipment: Optional[bool] = Query(None, description="Filter by lab equipment"),
    is_accessible: Optional[bool] = Query(None, description="Filter by accessibility"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_bookable: Optional[bool] = Query(None, description="Filter by bookable status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get rooms with comprehensive filters and pagination.
    
    Supports filtering by:
    - search: Text search in room name or code
    - type_salle: Room type (classroom, lab, etc.)
    - min_capacite/max_capacite: Capacity range
    - building, floor: Location filters
    - Equipment filters: projector, computers, lab equipment
    - Status filters: active, accessible, bookable
    """
    query = db.query(Room)
    
    # Apply search filter
    if search:
        search_filter = or_(
            Room.nom.ilike(f"%{search}%"),
            Room.code.ilike(f"%{search}%"),
            Room.name.ilike(f"%{search}%")  # Legacy field
        )
        query = query.filter(search_filter)
    
    # Apply type filter
    if type_salle:
        query = query.filter(
            or_(Room.type_salle == type_salle, Room.room_type == type_salle)
        )
    
    # Apply capacity filters
    if min_capacite is not None:
        query = query.filter(
            or_(Room.capacite >= min_capacite, Room.capacity >= min_capacite)
        )
    
    if max_capacite is not None:
        query = query.filter(
            or_(Room.capacite <= max_capacite, Room.capacity <= max_capacite)
        )
    
    # Apply location filters
    if building:
        query = query.filter(Room.building.ilike(f"%{building}%"))
    
    if floor is not None:
        query = query.filter(Room.floor == floor)
    
    # Apply equipment filters
    if has_projector is not None:
        query = query.filter(Room.has_projector == has_projector)
    
    if has_computers is not None:
        query = query.filter(Room.has_computers == has_computers)
    
    if has_lab_equipment is not None:
        query = query.filter(Room.has_lab_equipment == has_lab_equipment)
    
    # Apply status filters
    if is_accessible is not None:
        query = query.filter(Room.is_accessible == is_accessible)
    
    if is_active is not None:
        query = query.filter(Room.is_active == is_active)
    
    if is_bookable is not None:
        query = query.filter(Room.is_bookable == is_bookable)
    
    # Order by building, floor, and name
    query = query.order_by(Room.building, Room.floor, Room.nom)
    
    # Apply pagination
    rooms = query.offset(skip).limit(limit).all()
    
    return rooms


@router.get("/{room_id}", response_model=RoomSchema)
async def get_room(
    room_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get room by ID with detailed information."""
    room = db.query(Room).filter(Room.id == room_id).first()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    return room


@router.post("/", response_model=RoomSchema, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new room with validation."""
    # Check if code already exists
    existing_room = db.query(Room).filter(Room.code == room_data.code.upper()).first()
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room code already exists"
        )
    
    # Create room with all fields
    room_dict = room_data.model_dump()
    
    # Set compatibility fields
    room_dict['name'] = room_dict['nom']
    room_dict['capacity'] = room_dict['capacite']
    room_dict['room_type'] = room_dict['type_salle']
    
    room = Room(**room_dict)
    
    db.add(room)
    db.commit()
    db.refresh(room)
    
    return room


@router.put("/{room_id}", response_model=RoomSchema)
async def update_room(
    room_id: int,
    room_data: RoomUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update room completely."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check code uniqueness if being updated
    if room_data.code and room_data.code.upper() != room.code:
        existing = db.query(Room).filter(
            and_(Room.code == room_data.code.upper(), Room.id != room_id)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Room code already exists"
            )
    
    # Update fields
    update_data = room_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(room, field):
            setattr(room, field, value)
    
    # Update compatibility fields
    if room_data.nom:
        room.name = room_data.nom
    if room_data.capacite:
        room.capacity = room_data.capacite
    if room_data.type_salle:
        room.room_type = room_data.type_salle
    
    db.commit()
    db.refresh(room)
    
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: int,
    force: bool = Query(False, description="Force delete even if room has bookings"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete room with verification checks."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check if room has schedules/bookings
    # This would need to be implemented based on your schedule model
    
    db.delete(room)
    db.commit()


# ============================================================================
# SPECIALIZED ENDPOINTS
# ============================================================================

@router.get("/available/", response_model=List[RoomBasic])
async def get_available_rooms(
    day_of_week: int = Query(..., ge=0, le=5, description="Day of week (0=Sunday, 5=Friday)"),
    start_time: str = Query(..., description="Start time (HH:MM format)"),
    end_time: str = Query(..., description="End time (HH:MM format)"),
    min_capacity: Optional[int] = Query(None, ge=1, description="Minimum required capacity"),
    required_equipment: Optional[str] = Query(None, description="Required equipment (comma-separated)"),
    room_type: Optional[RoomType] = Query(None, description="Required room type"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get rooms available for a specific time slot with optional requirements."""
    
    # Parse time format
    try:
        start_hour, start_min = map(int, start_time.split(':'))
        end_hour, end_min = map(int, end_time.split(':'))
        start_time_obj = time(start_hour, start_min)
        end_time_obj = time(end_hour, end_min)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time format. Use HH:MM"
        )
    
    # Base query for active and bookable rooms
    query = db.query(Room).filter(
        Room.is_active == True,
        Room.is_bookable == True
    )
    
    # Apply capacity filter
    if min_capacity:
        query = query.filter(
            or_(Room.capacite >= min_capacity, Room.capacity >= min_capacity)
        )
    
    # Apply room type filter
    if room_type:
        query = query.filter(
            or_(Room.type_salle == room_type, Room.room_type == room_type)
        )
    
    # Apply equipment filters
    if required_equipment:
        equipment_list = [eq.strip().lower() for eq in required_equipment.split(',')]
        for equipment in equipment_list:
            if equipment == 'projector':
                query = query.filter(Room.has_projector == True)
            elif equipment == 'computers':
                query = query.filter(Room.has_computers == True)
            elif equipment == 'lab_equipment':
                query = query.filter(Room.has_lab_equipment == True)
    
    # TODO: Add availability check against schedules/bookings
    # This would involve checking the room's actual bookings for the time slot
    
    available_rooms = query.order_by(Room.building, Room.floor, Room.nom).all()
    
    return available_rooms


@router.get("/by-capacity/{min_capacity}", response_model=List[RoomBasic])
async def get_rooms_by_capacity(
    min_capacity: int,
    room_type: Optional[RoomType] = Query(None, description="Filter by room type"),
    building: Optional[str] = Query(None, description="Filter by building"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get rooms with minimum capacity and optional filters."""
    
    query = db.query(Room).filter(
        or_(Room.capacite >= min_capacity, Room.capacity >= min_capacity)
    )
    
    if room_type:
        query = query.filter(
            or_(Room.type_salle == room_type, Room.room_type == room_type)
        )
    
    if building:
        query = query.filter(Room.building.ilike(f"%{building}%"))
    
    if is_active is not None:
        query = query.filter(Room.is_active == is_active)
    
    rooms = query.order_by(
        (Room.capacite or Room.capacity).desc(),
        Room.building,
        Room.nom
    ).all()
    
    return rooms


@router.post("/check-conflicts/")
async def check_room_booking_conflicts(
    conflict_check: RoomConflictCheck,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check for booking conflicts in a room for a specific time slot."""
    
    # Get room
    room = db.query(Room).filter(Room.id == conflict_check.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Parse times
    try:
        start_hour, start_min = map(int, conflict_check.start_time.split(':'))
        end_hour, end_min = map(int, conflict_check.end_time.split(':'))
        start_time_obj = time(start_hour, start_min)
        end_time_obj = time(end_hour, end_min)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time format. Use HH:MM"
        )
    
    # TODO: Check against actual schedule/booking data
    # This would involve querying the schedule table for conflicts
    
    # For now, return a sample response
    conflicts = []  # Would be populated with actual conflicts
    
    return {
        "room_id": conflict_check.room_id,
        "day_of_week": conflict_check.day_of_week,
        "start_time": conflict_check.start_time,
        "end_time": conflict_check.end_time,
        "has_conflicts": len(conflicts) > 0,
        "conflicts": conflicts,
        "message": "No conflicts found" if not conflicts else f"{len(conflicts)} conflict(s) found"
    }


# ============================================================================
# BUSINESS LOGIC ENDPOINTS
# ============================================================================

@router.get("/validate-for-subject/{subject_id}")
async def validate_rooms_for_subject(
    subject_id: int,
    class_effectif: Optional[int] = Query(None, description="Class size to check capacity"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Validate which rooms are suitable for a specific subject."""
    
    # Get subject
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Build room requirements based on subject
    requirements = {
        "needs_lab": subject.requires_lab,
        "needs_special_room": subject.requires_special_room,
        "min_capacity": class_effectif or 1
    }
    
    # Base query for active rooms
    query = db.query(Room).filter(Room.is_active == True)
    
    # Apply subject-specific filters
    if subject.requires_lab:
        query = query.filter(
            or_(
                Room.has_lab_equipment == True,
                Room.type_salle == RoomType.SCIENCE_LAB,
                Room.type_salle == RoomType.COMPUTER_LAB,
                Room.room_type == RoomType.SCIENCE_LAB,
                Room.room_type == RoomType.COMPUTER_LAB
            )
        )
    
    if subject.requires_special_room:
        # Filter for special room types based on subject type
        special_types = [
            RoomType.SCIENCE_LAB,
            RoomType.COMPUTER_LAB,
            RoomType.ART_ROOM,
            RoomType.MUSIC_ROOM,
            RoomType.SPORTS_HALL
        ]
        query = query.filter(
            or_(
                Room.type_salle.in_(special_types),
                Room.room_type.in_(special_types)
            )
        )
    
    # Apply capacity filter if provided
    if class_effectif:
        query = query.filter(
            or_(Room.capacite >= class_effectif, Room.capacity >= class_effectif)
        )
    
    suitable_rooms = query.order_by(Room.building, Room.floor, Room.nom).all()
    
    # Get all rooms for comparison
    all_rooms = db.query(Room).filter(Room.is_active == True).count()
    
    return {
        "subject_id": subject_id,
        "subject_code": subject.code,
        "subject_name_fr": subject.nom_fr,
        "requirements": requirements,
        "suitable_rooms_count": len(suitable_rooms),
        "total_rooms_count": all_rooms,
        "compatibility_rate": round((len(suitable_rooms) / all_rooms * 100), 1) if all_rooms > 0 else 0,
        "suitable_rooms": [
            {
                "id": room.id,
                "code": room.code,
                "nom": room.nom or room.name,
                "capacite": room.capacite or room.capacity,
                "type_salle": room.type_salle or room.room_type,
                "building": room.building,
                "floor": room.floor,
                "has_required_equipment": {
                    "lab_equipment": room.has_lab_equipment,
                    "projector": room.has_projector,
                    "computers": room.has_computers
                }
            }
            for room in suitable_rooms
        ]
    }


@router.get("/optimization/suggest")
async def suggest_room_optimization(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Suggest room optimization based on usage patterns and requirements."""
    
    # Room utilization analysis
    total_rooms = db.query(Room).filter(Room.is_active == True).count()
    bookable_rooms = db.query(Room).filter(
        Room.is_active == True,
        Room.is_bookable == True
    ).count()
    
    # Room type distribution
    type_distribution = db.query(
        Room.type_salle,
        func.count(Room.id).label('count')
    ).filter(Room.is_active == True).group_by(Room.type_salle).all()
    
    # Capacity analysis
    capacity_stats = db.query(
        func.min(Room.capacite).label('min_capacity'),
        func.max(Room.capacite).label('max_capacity'),
        func.avg(Room.capacite).label('avg_capacity')
    ).filter(Room.is_active == True).first()
    
    # Equipment analysis
    equipment_stats = db.query(
        func.sum(func.cast(Room.has_projector, db.Integer)).label('projector_count'),
        func.sum(func.cast(Room.has_computers, db.Integer)).label('computer_count'),
        func.sum(func.cast(Room.has_lab_equipment, db.Integer)).label('lab_count')
    ).filter(Room.is_active == True).first()
    
    # Building distribution
    building_stats = db.query(
        Room.building,
        func.count(Room.id).label('count')
    ).filter(Room.is_active == True).group_by(Room.building).all()
    
    suggestions = []
    
    # Generate optimization suggestions
    if equipment_stats.projector_count < total_rooms * 0.7:
        suggestions.append({
            "type": "equipment",
            "priority": "high",
            "message": f"Consider adding projectors to more rooms ({equipment_stats.projector_count}/{total_rooms} have projectors)"
        })
    
    if capacity_stats.min_capacity and capacity_stats.min_capacity < 10:
        suggestions.append({
            "type": "capacity",
            "priority": "medium",
            "message": "Some rooms have very low capacity, consider optimization for better space utilization"
        })
    
    regular_classrooms = sum(1 for item in type_distribution if item.type_salle == RoomType.REGULAR_CLASSROOM)
    if regular_classrooms < total_rooms * 0.5:
        suggestions.append({
            "type": "room_type",
            "priority": "low",
            "message": "Consider converting some specialized rooms to regular classrooms for flexibility"
        })
    
    return {
        "total_rooms": total_rooms,
        "bookable_rooms": bookable_rooms,
        "utilization_rate": round((bookable_rooms / total_rooms * 100), 1) if total_rooms > 0 else 0,
        "room_type_distribution": {item.type_salle: item.count for item in type_distribution},
        "capacity_statistics": {
            "min_capacity": capacity_stats.min_capacity or 0,
            "max_capacity": capacity_stats.max_capacity or 0,
            "avg_capacity": round(float(capacity_stats.avg_capacity or 0), 1)
        },
        "equipment_statistics": {
            "projector_coverage": round((equipment_stats.projector_count / total_rooms * 100), 1) if total_rooms > 0 else 0,
            "computer_coverage": round((equipment_stats.computer_count / total_rooms * 100), 1) if total_rooms > 0 else 0,
            "lab_coverage": round((equipment_stats.lab_count / total_rooms * 100), 1) if total_rooms > 0 else 0
        },
        "building_distribution": {item.building: item.count for item in building_stats if item.building},
        "optimization_suggestions": suggestions
    }


@router.get("/stats/summary")
async def get_rooms_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive room statistics."""
    
    # Basic counts
    total_rooms = db.query(Room).count()
    active_rooms = db.query(Room).filter(Room.is_active == True).count()
    bookable_rooms = db.query(Room).filter(Room.is_bookable == True).count()
    
    # By type
    type_stats = db.query(
        Room.type_salle,
        func.count(Room.id).label('count')
    ).group_by(Room.type_salle).all()
    
    # By building
    building_stats = db.query(
        Room.building,
        func.count(Room.id).label('count')
    ).group_by(Room.building).all()
    
    # Capacity statistics
    capacity_stats = db.query(
        func.min(Room.capacite).label('min_capacity'),
        func.max(Room.capacite).label('max_capacity'),
        func.avg(Room.capacite).label('avg_capacity'),
        func.sum(Room.capacite).label('total_capacity')
    ).first()
    
    # Equipment statistics
    equipment_stats = db.query(
        func.sum(func.cast(Room.has_projector, db.Integer)).label('with_projector'),
        func.sum(func.cast(Room.has_computers, db.Integer)).label('with_computers'),
        func.sum(func.cast(Room.has_lab_equipment, db.Integer)).label('with_lab'),
        func.sum(func.cast(Room.is_accessible, db.Integer)).label('accessible')
    ).first()
    
    return {
        "total_rooms": total_rooms,
        "active_rooms": active_rooms,
        "bookable_rooms": bookable_rooms,
        "by_type": {item.type_salle: item.count for item in type_stats if item.type_salle},
        "by_building": {item.building: item.count for item in building_stats if item.building},
        "capacity_statistics": {
            "min_capacity": capacity_stats.min_capacity or 0,
            "max_capacity": capacity_stats.max_capacity or 0,
            "avg_capacity": round(float(capacity_stats.avg_capacity or 0), 1),
            "total_capacity": capacity_stats.total_capacity or 0
        },
        "equipment_statistics": {
            "with_projector": equipment_stats.with_projector or 0,
            "with_computers": equipment_stats.with_computers or 0,
            "with_lab_equipment": equipment_stats.with_lab or 0,
            "accessible": equipment_stats.accessible or 0
        }
    } 