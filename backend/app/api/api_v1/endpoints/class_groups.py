"""
Class Groups management endpoints - Complete CRUD API.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from math import ceil

from app.core.auth import get_current_active_user
from app.db.base import get_db
from app.models.user import User
from app.models.class_group import ClassGroup
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.schemas.class_group import (
    ClassGroup as ClassGroupSchema,
    ClassGroupCreate,
    ClassGroupUpdate,
    ClassGroupBasic,
    ClassGroupWithSubjects,
    ClassSubjectAssignment
)
from app.schemas.subject import SubjectBasic

router = APIRouter()


# ============================================================================
# MAIN CRUD ENDPOINTS
# ============================================================================

@router.get("/", response_model=List[ClassGroupWithSubjects])
async def get_class_groups(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search in name or code"),
    niveau: Optional[str] = Query(None, description="Filter by level"),
    class_type: Optional[str] = Query(None, description="Filter by class type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    min_effectif: Optional[int] = Query(None, ge=1, description="Minimum number of students"),
    max_effectif: Optional[int] = Query(None, ge=1, description="Maximum number of students"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get class groups with optional filters and pagination.
    
    Supports filtering by:
    - search: Text search in class name or code
    - niveau: Class level (e.g., "6ème", "5ème")
    - class_type: Type of class (regular/advanced/special_needs)
    - is_active: Active/inactive status
    - min_effectif/max_effectif: Student count range
    - academic_year: Academic year
    """
    query = db.query(ClassGroup).options(
        joinedload(ClassGroup.matieres_obligatoires),
        joinedload(ClassGroup.homeroom_teacher)
    )
    
    # Apply filters
    if search:
        search_filter = or_(
            ClassGroup.nom.ilike(f"%{search}%"),
            ClassGroup.code.ilike(f"%{search}%"),
            ClassGroup.name.ilike(f"%{search}%")  # Legacy field
        )
        query = query.filter(search_filter)
    
    if niveau:
        query = query.filter(ClassGroup.niveau.ilike(f"%{niveau}%"))
    
    if class_type:
        query = query.filter(ClassGroup.class_type == class_type)
    
    if is_active is not None:
        query = query.filter(ClassGroup.is_active == is_active)
    
    if min_effectif is not None:
        query = query.filter(ClassGroup.effectif >= min_effectif)
    
    if max_effectif is not None:
        query = query.filter(ClassGroup.effectif <= max_effectif)
    
    if academic_year:
        query = query.filter(ClassGroup.academic_year == academic_year)
    
    # Order by level and name
    query = query.order_by(ClassGroup.niveau, ClassGroup.nom)
    
    # Apply pagination
    class_groups = query.offset(skip).limit(limit).all()
    
    return class_groups


@router.get("/{class_group_id}", response_model=ClassGroupWithSubjects)
async def get_class_group(
    class_group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get class group by ID with complete details."""
    class_group = db.query(ClassGroup).options(
        joinedload(ClassGroup.matieres_obligatoires),
        joinedload(ClassGroup.homeroom_teacher)
    ).filter(ClassGroup.id == class_group_id).first()
    
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class group not found"
        )
    
    return class_group


@router.post("/", response_model=ClassGroupSchema, status_code=status.HTTP_201_CREATED)
async def create_class_group(
    class_group_data: ClassGroupCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new class group with optional subjects."""
    # Check if code already exists
    existing_class = db.query(ClassGroup).filter(ClassGroup.code == class_group_data.code.upper()).first()
    if existing_class:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class group code already exists"
        )
    
    # Create class group
    class_dict = class_group_data.model_dump(exclude={"subject_ids"})
    
    # Set compatibility fields
    class_dict['name'] = class_dict['nom']
    class_dict['student_count'] = class_dict['effectif']
    
    class_group = ClassGroup(**class_dict)
    
    # Add subjects if provided
    if class_group_data.subject_ids:
        subjects = db.query(Subject).filter(Subject.id.in_(class_group_data.subject_ids)).all()
        if len(subjects) != len(class_group_data.subject_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more subject IDs not found"
            )
        class_group.matieres_obligatoires = subjects
    
    db.add(class_group)
    db.commit()
    db.refresh(class_group)
    
    return class_group


@router.put("/{class_group_id}", response_model=ClassGroupSchema)
async def update_class_group(
    class_group_id: int,
    class_group_data: ClassGroupUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update class group completely."""
    class_group = db.query(ClassGroup).filter(ClassGroup.id == class_group_id).first()
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class group not found"
        )
    
    # Check code uniqueness if being updated
    if class_group_data.code and class_group_data.code.upper() != class_group.code:
        existing = db.query(ClassGroup).filter(
            and_(ClassGroup.code == class_group_data.code.upper(), ClassGroup.id != class_group_id)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class group code already exists"
            )
    
    # Update fields
    update_data = class_group_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(class_group, field):
            setattr(class_group, field, value)
    
    # Update compatibility fields
    if class_group_data.nom:
        class_group.name = class_group_data.nom
    if class_group_data.effectif:
        class_group.student_count = class_group_data.effectif
    
    db.commit()
    db.refresh(class_group)
    
    return class_group


@router.delete("/{class_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class_group(
    class_group_id: int,
    force: bool = Query(False, description="Force delete even if class has schedules"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete class group with verification checks."""
    class_group = db.query(ClassGroup).filter(ClassGroup.id == class_group_id).first()
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class group not found"
        )
    
    # Check if class has schedules (if schedule model exists)
    # This would need to be implemented based on your schedule model
    
    # Remove subject associations
    class_group.matieres_obligatoires.clear()
    
    db.delete(class_group)
    db.commit()


# ============================================================================
# SUBJECT MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/{class_group_id}/subjects", response_model=List[SubjectBasic])
async def get_class_group_subjects(
    class_group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all subjects assigned to a class group."""
    class_group = db.query(ClassGroup).options(
        joinedload(ClassGroup.matieres_obligatoires)
    ).filter(ClassGroup.id == class_group_id).first()
    
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class group not found"
        )
    
    return class_group.matieres_obligatoires


@router.post("/{class_group_id}/subjects", status_code=status.HTTP_201_CREATED)
async def assign_subjects_to_class_group(
    class_group_id: int,
    assignment: ClassSubjectAssignment,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Assign multiple subjects to a class group."""
    # Get class group
    class_group = db.query(ClassGroup).filter(ClassGroup.id == class_group_id).first()
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class group not found"
        )
    
    # Get subjects
    subjects = db.query(Subject).filter(Subject.id.in_(assignment.subject_ids)).all()
    if len(subjects) != len(assignment.subject_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more subject IDs not found"
        )
    
    # Check for already assigned subjects
    current_subject_ids = {s.id for s in class_group.matieres_obligatoires}
    new_subject_ids = set(assignment.subject_ids)
    already_assigned = current_subject_ids.intersection(new_subject_ids)
    
    if already_assigned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subjects already assigned: {list(already_assigned)}"
        )
    
    # Assign subjects
    class_group.matieres_obligatoires.extend(subjects)
    db.commit()
    
    return {"message": f"Successfully assigned {len(subjects)} subjects to class group"}


@router.delete("/{class_group_id}/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_subject_from_class_group(
    class_group_id: int,
    subject_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a subject from a class group."""
    # Get class group
    class_group = db.query(ClassGroup).filter(ClassGroup.id == class_group_id).first()
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class group not found"
        )
    
    # Get subject
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Check if assigned
    if subject not in class_group.matieres_obligatoires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject not assigned to this class group"
        )
    
    # Remove subject
    class_group.matieres_obligatoires.remove(subject)
    db.commit()


# ============================================================================
# SPECIALIZED ENDPOINTS
# ============================================================================

@router.get("/by-level/{niveau}", response_model=List[ClassGroupBasic])
async def get_class_groups_by_level(
    niveau: str,
    class_type: Optional[str] = Query(None, description="Filter by class type"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get class groups by level with optional filters."""
    
    query = db.query(ClassGroup).filter(ClassGroup.niveau.ilike(f"%{niveau}%"))
    
    if class_type:
        query = query.filter(ClassGroup.class_type == class_type)
    
    if is_active is not None:
        query = query.filter(ClassGroup.is_active == is_active)
    
    class_groups = query.order_by(ClassGroup.nom).all()
    
    return class_groups


@router.get("/stats/summary")
async def get_class_groups_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get class groups statistics summary."""
    
    # Basic counts
    total_classes = db.query(ClassGroup).count()
    active_classes = db.query(ClassGroup).filter(ClassGroup.is_active == True).count()
    
    # By type
    type_stats = db.query(
        ClassGroup.class_type,
        func.count(ClassGroup.id).label('count')
    ).group_by(ClassGroup.class_type).all()
    
    # By level
    level_stats = db.query(
        ClassGroup.niveau,
        func.count(ClassGroup.id).label('count')
    ).group_by(ClassGroup.niveau).all()
    
    # Student statistics
    student_stats = db.query(
        func.sum(ClassGroup.effectif).label('total_students'),
        func.avg(ClassGroup.effectif).label('avg_class_size'),
        func.min(ClassGroup.effectif).label('min_class_size'),
        func.max(ClassGroup.effectif).label('max_class_size')
    ).first()
    
    # Classes with/without subjects
    classes_with_subjects = db.query(ClassGroup).join(ClassGroup.matieres_obligatoires).distinct().count()
    classes_without_subjects = total_classes - classes_with_subjects
    
    return {
        "total_classes": total_classes,
        "active_classes": active_classes,
        "by_type": {item.class_type: item.count for item in type_stats},
        "by_level": {item.niveau: item.count for item in level_stats},
        "student_statistics": {
            "total_students": student_stats.total_students or 0,
            "avg_class_size": round(float(student_stats.avg_class_size or 0), 1),
            "min_class_size": student_stats.min_class_size or 0,
            "max_class_size": student_stats.max_class_size or 0
        },
        "subject_assignment": {
            "with_subjects": classes_with_subjects,
            "without_subjects": classes_without_subjects
        }
    }


# ============================================================================
# CAPACITY AND OPTIMIZATION ENDPOINTS
# ============================================================================

@router.get("/capacity-check/{class_group_id}")
async def check_class_room_capacity_compatibility(
    class_group_id: int,
    room_id: Optional[int] = Query(None, description="Specific room ID to check"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check if class group size is compatible with available rooms."""
    # Get class group
    class_group = db.query(ClassGroup).filter(ClassGroup.id == class_group_id).first()
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class group not found"
        )
    
    from app.models.room import Room
    
    if room_id:
        # Check specific room
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found"
            )
        
        compatible = (room.capacite or room.capacity or 0) >= class_group.effectif
        return {
            "class_group_id": class_group_id,
            "effectif": class_group.effectif,
            "room_id": room_id,
            "room_capacity": room.capacite or room.capacity,
            "compatible": compatible,
            "capacity_difference": (room.capacite or room.capacity or 0) - class_group.effectif
        }
    else:
        # Find all compatible rooms
        query = db.query(Room).filter(
            Room.is_active == True,
            Room.is_bookable == True
        )
        
        # Filter by capacity
        if Room.capacite:
            query = query.filter(Room.capacite >= class_group.effectif)
        else:
            query = query.filter(Room.capacity >= class_group.effectif)
        
        compatible_rooms = query.all()
        
        return {
            "class_group_id": class_group_id,
            "effectif": class_group.effectif,
            "compatible_rooms_count": len(compatible_rooms),
            "compatible_rooms": [
                {
                    "id": room.id,
                    "code": room.code,
                    "nom": room.nom or room.name,
                    "capacite": room.capacite or room.capacity,
                    "type_salle": room.type_salle or room.room_type,
                    "capacity_margin": (room.capacite or room.capacity or 0) - class_group.effectif
                }
                for room in compatible_rooms
            ]
        }


 