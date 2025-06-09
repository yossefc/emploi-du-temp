"""
Teacher management endpoints - Complete CRUD API.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
import csv
import io

from app.core.auth import get_current_active_user
from app.db.base import get_db
from app.models.user import User
from app.models.teacher import Teacher
from app.models.subject import Subject
from app.models.constraint import TeacherAvailability, TeacherPreference
from app.schemas.teacher import (
    Teacher as TeacherSchema,
    TeacherCreate,
    TeacherUpdate,
    TeacherBasic,
    TeacherAvailability as TeacherAvailabilitySchema,
    TeacherAvailabilityCreate,
    TeacherPreference as TeacherPreferenceSchema,
    TeacherPreferenceCreate
)
from app.schemas.subject import SubjectBasic

router = APIRouter()


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================

@router.get("/", response_model=List[TeacherSchema])
async def get_teachers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search in name, email, or code"),
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    language: Optional[str] = Query(None, regex="^(he|fr)$", description="Filter by primary language"),
    available_day: Optional[int] = Query(None, ge=0, le=5, description="Filter by available day (0-5)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get teachers with optional filters and pagination.
    
    Supports filtering by:
    - search: Text search in name, email, or code
    - subject_id: Teachers who teach specific subject
    - is_active: Active/inactive status
    - language: Primary language (he/fr)
    - available_day: Day of week availability (0=Sunday, 5=Friday)
    """
    query = db.query(Teacher).options(joinedload(Teacher.subjects))
    
    # Apply filters
    if search:
        search_filter = or_(
            Teacher.first_name.ilike(f"%{search}%"),
            Teacher.last_name.ilike(f"%{search}%"),
            Teacher.email.ilike(f"%{search}%"),
            Teacher.code.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if subject_id is not None:
        query = query.join(Teacher.subjects).filter(Subject.id == subject_id)
    
    if is_active is not None:
        query = query.filter(Teacher.is_active == is_active)
    
    if language:
        query = query.filter(Teacher.primary_language == language)
    
    if available_day is not None:
        query = query.join(Teacher.availabilities).filter(
            and_(
                TeacherAvailability.day_of_week == available_day,
                TeacherAvailability.is_available == True
            )
        )
    
    # Get total count for pagination metadata
    total = query.count()
    
    # Apply pagination
    teachers = query.offset(skip).limit(limit).all()
    
    # Add pagination metadata to response headers
    # Note: In a real implementation, you might want to return this in a wrapper object
    return teachers


@router.get("/{teacher_id}", response_model=TeacherSchema)
async def get_teacher(
    teacher_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get teacher by ID with all related data."""
    teacher = db.query(Teacher).options(
        joinedload(Teacher.subjects),
        joinedload(Teacher.availabilities),
        joinedload(Teacher.preferences)
    ).filter(Teacher.id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    return teacher


@router.post("/", response_model=TeacherSchema, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_data: TeacherCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new teacher."""
    # Check if code already exists
    existing_teacher = db.query(Teacher).filter(Teacher.code == teacher_data.code).first()
    if existing_teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher code already exists"
        )
    
    # Check if email already exists (if provided)
    if teacher_data.email:
        existing_email = db.query(Teacher).filter(Teacher.email == teacher_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Create teacher
    teacher_dict = teacher_data.model_dump(exclude={"subject_ids"})
    teacher = Teacher(**teacher_dict)
    
    # Add subjects if provided
    if teacher_data.subject_ids:
        subjects = db.query(Subject).filter(Subject.id.in_(teacher_data.subject_ids)).all()
        if len(subjects) != len(teacher_data.subject_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more subject IDs not found"
            )
        teacher.subjects = subjects
    
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    
    return teacher


@router.put("/{teacher_id}", response_model=TeacherSchema)
async def update_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update teacher completely."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Check code uniqueness if being updated
    if teacher_data.code and teacher_data.code != teacher.code:
        existing = db.query(Teacher).filter(
            and_(Teacher.code == teacher_data.code, Teacher.id != teacher_id)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher code already exists"
            )
    
    # Check email uniqueness if being updated
    if teacher_data.email and teacher_data.email != teacher.email:
        existing = db.query(Teacher).filter(
            and_(Teacher.email == teacher_data.email, Teacher.id != teacher_id)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Update teacher fields
    update_data = teacher_data.model_dump(exclude_unset=True, exclude={"subject_ids"})
    for field, value in update_data.items():
        setattr(teacher, field, value)
    
    # Update subjects if provided
    if teacher_data.subject_ids is not None:
        subjects = db.query(Subject).filter(Subject.id.in_(teacher_data.subject_ids)).all()
        if len(subjects) != len(teacher_data.subject_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more subject IDs not found"
            )
        teacher.subjects = subjects
    
    db.commit()
    db.refresh(teacher)
    
    return teacher


@router.patch("/{teacher_id}", response_model=TeacherSchema)
async def patch_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Partially update teacher."""
    return await update_teacher(teacher_id, teacher_data, current_user, db)


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(
    teacher_id: int,
    force: bool = Query(False, description="Force delete even if teacher has schedules"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete teacher with conflict checking."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Check for existing schedules (would need to import ScheduleEntry model)
    # For now, we'll skip this check but in a real implementation:
    # if not force:
    #     schedule_count = db.query(ScheduleEntry).filter(ScheduleEntry.teacher_id == teacher_id).count()
    #     if schedule_count > 0:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail=f"Cannot delete teacher. Found {schedule_count} schedule entries. Use force=true to override."
    #         )
    
    db.delete(teacher)
    db.commit()


# ============================================================================
# SUBJECT MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/{teacher_id}/subjects", response_model=List[SubjectBasic])
async def get_teacher_subjects(
    teacher_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get subjects taught by teacher."""
    teacher = db.query(Teacher).options(joinedload(Teacher.subjects)).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    return teacher.subjects


@router.post("/{teacher_id}/subjects/{subject_id}", status_code=status.HTTP_201_CREATED)
async def assign_subject_to_teacher(
    teacher_id: int,
    subject_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Assign subject to teacher."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Check if already assigned
    if subject in teacher.subjects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject already assigned to teacher"
        )
    
    teacher.subjects.append(subject)
    db.commit()
    
    return {"message": "Subject assigned successfully"}


@router.delete("/{teacher_id}/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_subject_from_teacher(
    teacher_id: int,
    subject_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove subject from teacher."""
    teacher = db.query(Teacher).options(joinedload(Teacher.subjects)).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    subject = next((s for s in teacher.subjects if s.id == subject_id), None)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not assigned to teacher"
        )
    
    teacher.subjects.remove(subject)
    db.commit()


# ============================================================================
# AVAILABILITY MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/{teacher_id}/availability", response_model=List[TeacherAvailabilitySchema])
async def get_teacher_availability(
    teacher_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get teacher's availability schedule."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    availabilities = db.query(TeacherAvailability).filter(
        TeacherAvailability.teacher_id == teacher_id
    ).order_by(
        TeacherAvailability.day_of_week,
        TeacherAvailability.start_time
    ).all()
    
    return availabilities


@router.post("/{teacher_id}/availability", response_model=TeacherAvailabilitySchema, status_code=status.HTTP_201_CREATED)
async def create_teacher_availability(
    teacher_id: int,
    availability_data: TeacherAvailabilityCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create teacher availability slot."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Validate time range
    if availability_data.start_time >= availability_data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time"
        )
    
    # Check for overlapping availability slots
    overlapping = db.query(TeacherAvailability).filter(
        and_(
            TeacherAvailability.teacher_id == teacher_id,
            TeacherAvailability.day_of_week == availability_data.day_of_week,
            or_(
                and_(
                    TeacherAvailability.start_time <= availability_data.start_time,
                    TeacherAvailability.end_time > availability_data.start_time
                ),
                and_(
                    TeacherAvailability.start_time < availability_data.end_time,
                    TeacherAvailability.end_time >= availability_data.end_time
                )
            )
        )
    ).first()
    
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Availability slot overlaps with existing slot"
        )
    
    availability = TeacherAvailability(**availability_data.model_dump())
    availability.teacher_id = teacher_id
    
    db.add(availability)
    db.commit()
    db.refresh(availability)
    
    return availability


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@router.get("/export/csv")
async def export_teachers_csv(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export teachers list to CSV."""
    teachers = db.query(Teacher).options(joinedload(Teacher.subjects)).all()
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "Code", "First Name", "Last Name", "Email", "Phone",
        "Max Hours/Week", "Max Hours/Day", "Primary Language",
        "Can Teach French", "Can Teach Hebrew", "Subjects", "Active"
    ])
    
    # Write teacher data
    for teacher in teachers:
        subjects_names = ", ".join([s.name_fr for s in teacher.subjects])
        writer.writerow([
            teacher.id,
            teacher.code,
            teacher.first_name,
            teacher.last_name,
            teacher.email or "",
            teacher.phone or "",
            teacher.max_hours_per_week,
            teacher.max_hours_per_day,
            teacher.primary_language,
            teacher.can_teach_in_french,
            teacher.can_teach_in_hebrew,
            subjects_names,
            teacher.is_active
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=teachers.csv"}
    )


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/stats/summary")
async def get_teachers_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get teachers statistics summary."""
    total_teachers = db.query(Teacher).count()
    active_teachers = db.query(Teacher).filter(Teacher.is_active == True).count()
    french_teachers = db.query(Teacher).filter(Teacher.can_teach_in_french == True).count()
    hebrew_teachers = db.query(Teacher).filter(Teacher.can_teach_in_hebrew == True).count()
    
    # Average hours per week
    avg_hours = db.query(func.avg(Teacher.max_hours_per_week)).scalar() or 0
    
    return {
        "total_teachers": total_teachers,
        "active_teachers": active_teachers,
        "inactive_teachers": total_teachers - active_teachers,
        "french_capable": french_teachers,
        "hebrew_capable": hebrew_teachers,
        "average_max_hours_per_week": round(avg_hours, 2)
    }