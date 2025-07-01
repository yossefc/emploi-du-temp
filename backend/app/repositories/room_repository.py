"""
Room repository with specialized queries.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.repositories.base import BaseRepository
from app.models.room import Room, RoomType
from app.core.exceptions import DatabaseException


class RoomRepository(BaseRepository[Room]):
    """Repository for Room entities with specialized queries."""
    
    def __init__(self, db: Session):
        super().__init__(Room, db)
    
    def get_by_code(self, code: str) -> Optional[Room]:
        """Get room by code."""
        return self.get_by_field("code", code.upper())
    
    def get_active_rooms(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "code"
    ) -> List[Room]:
        """Get all active rooms."""
        return self.get_by_filters(
            filters={"is_active": True},
            skip=skip,
            limit=limit,
            order_by=order_by
        )
    
    def get_bookable_rooms(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Room]:
        """Get all bookable rooms."""
        return self.get_by_filters(
            filters={"is_active": True, "is_bookable": True},
            skip=skip,
            limit=limit,
            order_by="code"
        )
    
    def get_rooms_by_type(self, room_type: RoomType) -> List[Room]:
        """Get rooms by type."""
        return self.get_by_filters({
            "is_active": True,
            "room_type": room_type
        })
    
    def get_rooms_by_capacity_range(
        self, 
        min_capacity: int, 
        max_capacity: Optional[int] = None
    ) -> List[Room]:
        """Get rooms within capacity range."""
        try:
            query = (
                self.db.query(Room)
                .filter(Room.is_active == True)
                .filter(Room.capacity >= min_capacity)
            )
            
            if max_capacity:
                query = query.filter(Room.capacity <= max_capacity)
            
            return query.order_by(Room.capacity).all()
        except Exception as e:
            raise DatabaseException("get_rooms_by_capacity_range", e)
    
    def get_rooms_by_building(self, building: str) -> List[Room]:
        """Get rooms in a specific building."""
        return self.get_by_filters({
            "is_active": True,
            "building": building
        })
    
    def get_rooms_by_floor(self, floor: int) -> List[Room]:
        """Get rooms on a specific floor."""
        return self.get_by_filters({
            "is_active": True,
            "floor": floor
        })
    
    def get_accessible_rooms(self) -> List[Room]:
        """Get wheelchair accessible rooms."""
        return self.get_by_filters({
            "is_active": True,
            "is_accessible": True
        })
    
    def get_labs(self) -> List[Room]:
        """Get all laboratory rooms."""
        lab_types = [RoomType.SCIENCE_LAB, RoomType.COMPUTER_LAB, RoomType.LABORATORY]
        try:
            return (
                self.db.query(Room)
                .filter(Room.is_active == True)
                .filter(Room.room_type.in_(lab_types))
                .order_by(Room.code)
                .all()
            )
        except Exception as e:
            raise DatabaseException("get_labs", e)
    
    def get_rooms_with_equipment(self, equipment_type: str) -> List[Room]:
        """Get rooms with specific equipment."""
        equipment_filters = {
            "is_active": True
        }
        
        if equipment_type == "projector":
            equipment_filters["has_projector"] = True
        elif equipment_type == "computers":
            equipment_filters["has_computers"] = True
        elif equipment_type == "lab_equipment":
            equipment_filters["has_lab_equipment"] = True
        elif equipment_type == "air_conditioning":
            equipment_filters["has_air_conditioning"] = True
        
        return self.get_by_filters(equipment_filters)
    
    def get_rooms_requiring_supervision(self) -> List[Room]:
        """Get rooms that require supervision."""
        return self.get_by_filters({
            "is_active": True,
            "requires_supervision": True
        })
    
    def get_prayer_suitable_rooms(self) -> List[Room]:
        """Get rooms suitable for prayer."""
        return self.get_by_filters({
            "is_active": True,
            "suitable_for_prayer": True
        })
    
    def get_gender_restricted_rooms(self, gender: Optional[str] = None) -> List[Room]:
        """Get gender-restricted rooms."""
        filters = {"is_active": True}
        
        if gender:
            filters["gender_restricted"] = gender
        else:
            # Get all gender-restricted rooms
            try:
                return (
                    self.db.query(Room)
                    .filter(Room.is_active == True)
                    .filter(Room.gender_restricted.isnot(None))
                    .order_by(Room.code)
                    .all()
                )
            except Exception as e:
                raise DatabaseException("get_gender_restricted_rooms", e)
        
        return self.get_by_filters(filters)
    
    def search_rooms(
        self, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Room]:
        """Search rooms by code, name, or location."""
        if not search_term:
            return self.get_active_rooms(skip, limit)
        
        search_pattern = f"%{search_term.lower()}%"
        
        try:
            return (
                self.db.query(Room)
                .filter(
                    and_(
                        Room.is_active == True,
                        or_(
                            func.lower(Room.code).like(search_pattern),
                            func.lower(Room.name).like(search_pattern),
                            func.lower(Room.building).like(search_pattern),
                            func.lower(Room.location_details).like(search_pattern)
                        )
                    )
                )
                .order_by(Room.code)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            raise DatabaseException("search_rooms", e)
    
    def get_available_rooms_for_capacity(self, required_capacity: int) -> List[Room]:
        """Get available rooms that can accommodate the required capacity."""
        return self.get_by_filters({
            "is_active": True,
            "is_bookable": True
        })
    
    def get_rooms_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of room information."""
        try:
            total_rooms = self.count({"is_active": True})
            bookable_rooms = self.count({"is_active": True, "is_bookable": True})
            accessible_rooms = self.count({"is_active": True, "is_accessible": True})
            
            # Average capacity
            result = self.db.query(
                func.avg(Room.capacity),
                func.sum(Room.capacity)
            ).filter(Room.is_active == True).first()
            
            avg_capacity = round(result[0], 1) if result[0] else 0
            total_capacity = result[1] if result[1] else 0
            
            # By type
            type_counts = {}
            for room_type in RoomType:
                count = self.count({
                    "is_active": True,
                    "room_type": room_type
                })
                type_counts[room_type.value] = count
            
            return {
                "total_rooms": total_rooms,
                "bookable_rooms": bookable_rooms,
                "accessible_rooms": accessible_rooms,
                "total_capacity": total_capacity,
                "average_capacity": avg_capacity,
                "by_type": type_counts
            }
        except Exception as e:
            raise DatabaseException("get_rooms_summary", e) 