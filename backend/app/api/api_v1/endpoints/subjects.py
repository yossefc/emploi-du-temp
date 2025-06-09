"""
Subject management endpoints - Complete CRUD API with bilingual support.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from math import ceil

from app.core.auth import get_current_active_user
from app.db.base import get_db
from app.models.user import User
from app.models.subject import Subject, SubjectType
from app.models.teacher import Teacher
from app.schemas.subject import (
    Subject as SubjectSchema,
    SubjectCreate,
    SubjectUpdate,
    SubjectBasic,
    SubjectWithTeachers,
    SubjectSearch
)
from app.schemas.teacher import TeacherBasic

router = APIRouter()


# ============================================================================
# MAIN CRUD ENDPOINTS
# ============================================================================

@router.get("/", response_model=List[SubjectSchema])
async def get_subjects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search in names or code"),
    niveau: Optional[str] = Query(None, description="Filter by required level"),
    type_matiere: Optional[SubjectType] = Query(None, description="Filter by subject type"),
    langue: Optional[str] = Query(None, regex="^(fr|he)$", description="Filter by language preference"),
    heures_min: Optional[int] = Query(None, ge=1, le=40, description="Minimum hours per week"),
    heures_max: Optional[int] = Query(None, ge=1, le=40, description="Maximum hours per week"),
    requires_lab: Optional[bool] = Query(None, description="Filter by lab requirement"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get subjects with multilingual filters and pagination.
    
    Supports filtering by:
    - search: Text search in French/Hebrew names or code
    - niveau: Required level (e.g., "6ème", "5ème")
    - type_matiere: Subject type (obligatoire/optionnelle/spécialisée)
    - langue: Language preference for search (fr/he)
    - heures_min/heures_max: Hours per week range
    - requires_lab: Laboratory requirement
    """
    query = db.query(Subject)
    
    # Apply search filter (multilingual)
    if search:
        if langue == "he":
            # Hebrew search - focus on Hebrew name
            search_filter = or_(
                Subject.nom_he.ilike(f"%{search}%"),
                Subject.code.ilike(f"%{search}%")
            )
        elif langue == "fr":
            # French search - focus on French name
            search_filter = or_(
                Subject.nom_fr.ilike(f"%{search}%"),
                Subject.code.ilike(f"%{search}%")
            )
        else:
            # General search - both languages
            search_filter = or_(
                Subject.nom_fr.ilike(f"%{search}%"),
                Subject.nom_he.ilike(f"%{search}%"),
                Subject.code.ilike(f"%{search}%")
            )
        query = query.filter(search_filter)
    
    # Apply other filters
    if niveau:
        query = query.filter(Subject.niveau_requis.ilike(f"%{niveau}%"))
    
    if type_matiere:
        query = query.filter(Subject.type_matiere == type_matiere)
    
    if heures_min is not None:
        query = query.filter(Subject.heures_semaine >= heures_min)
    
    if heures_max is not None:
        query = query.filter(Subject.heures_semaine <= heures_max)
    
    if requires_lab is not None:
        query = query.filter(Subject.requires_lab == requires_lab)
    
    # Order by French name for consistent results
    query = query.order_by(Subject.nom_fr)
    
    # Apply pagination
    subjects = query.offset(skip).limit(limit).all()
    
    return subjects


@router.get("/{subject_id}", response_model=SubjectWithTeachers)
async def get_subject(
    subject_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get subject by ID with assigned teachers."""
    subject = db.query(Subject).options(
        joinedload(Subject.teachers)
    ).filter(Subject.id == subject_id).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return subject


@router.post("/", response_model=SubjectSchema, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: SubjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new subject with bilingual validation."""
    # Check if code already exists
    existing_subject = db.query(Subject).filter(Subject.code == subject_data.code.upper()).first()
    if existing_subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject code already exists"
        )
    
    # Create subject with all fields
    subject_dict = subject_data.model_dump()
    
    # Ensure compatibility fields are set
    subject_dict['name_fr'] = subject_dict['nom_fr']
    subject_dict['name_he'] = subject_dict['nom_he']
    subject_dict['subject_type'] = subject_dict['type_matiere']
    
    subject = Subject(**subject_dict)
    
    db.add(subject)
    db.commit()
    db.refresh(subject)
    
    return subject


@router.put("/{subject_id}", response_model=SubjectSchema)
async def update_subject(
    subject_id: int,
    subject_data: SubjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update subject completely."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Check code uniqueness if being updated
    if subject_data.code and subject_data.code.upper() != subject.code:
        existing = db.query(Subject).filter(
            and_(Subject.code == subject_data.code.upper(), Subject.id != subject_id)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject code already exists"
            )
    
    # Update fields
    update_data = subject_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(subject, field):
            setattr(subject, field, value)
    
    # Update compatibility fields
    if subject_data.nom_fr:
        subject.name_fr = subject_data.nom_fr
    if subject_data.nom_he:
        subject.name_he = subject_data.nom_he
    if subject_data.type_matiere:
        subject.subject_type = subject_data.type_matiere
    
    db.commit()
    db.refresh(subject)
    
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: int,
    force: bool = Query(False, description="Force delete even if subject has teachers or schedules"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete subject with verification checks."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Check if subject has assigned teachers
    if subject.teachers and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete subject: {len(subject.teachers)} teachers are assigned. Use force=true to override."
        )
    
    # Check if subject is used in schedules (if schedule model exists)
    # This would need to be implemented based on your schedule model
    
    # Remove teacher associations
    subject.teachers.clear()
    
    db.delete(subject)
    db.commit()


# ============================================================================
# SPECIALIZED ENDPOINTS
# ============================================================================

@router.get("/search/", response_model=SubjectSearch)
async def search_subjects(
    q: str = Query(..., min_length=1, description="Search query"),
    langue: Optional[str] = Query(None, regex="^(fr|he)$", description="Search language"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Advanced search for subjects by name or code with pagination."""
    
    # Build search query
    if langue == "he":
        search_filter = or_(
            Subject.nom_he.ilike(f"%{q}%"),
            Subject.code.ilike(f"%{q}%")
        )
    elif langue == "fr":
        search_filter = or_(
            Subject.nom_fr.ilike(f"%{q}%"),
            Subject.code.ilike(f"%{q}%")
        )
    else:
        search_filter = or_(
            Subject.nom_fr.ilike(f"%{q}%"),
            Subject.nom_he.ilike(f"%{q}%"),
            Subject.code.ilike(f"%{q}%")
        )
    
    query = db.query(Subject).filter(search_filter)
    
    # Get total count
    total = query.count()
    total_pages = ceil(total / per_page)
    
    # Apply pagination
    skip = (page - 1) * per_page
    subjects = query.order_by(Subject.nom_fr).offset(skip).limit(per_page).all()
    
    return SubjectSearch(
        subjects=subjects,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/by-level/{level}", response_model=List[SubjectSchema])
async def get_subjects_by_level(
    level: str,
    type_matiere: Optional[SubjectType] = Query(None, description="Filter by subject type"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get subjects by required level with optional type filter."""
    
    query = db.query(Subject).filter(Subject.niveau_requis.ilike(f"%{level}%"))
    
    if type_matiere:
        query = query.filter(Subject.type_matiere == type_matiere)
    
    subjects = query.order_by(Subject.nom_fr).all()
    
    return subjects


# ============================================================================
# RELATIONSHIP ENDPOINTS
# ============================================================================

@router.get("/{subject_id}/teachers", response_model=List[TeacherBasic])
async def get_subject_teachers(
    subject_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all teachers assigned to a subject."""
    subject = db.query(Subject).options(
        joinedload(Subject.teachers)
    ).filter(Subject.id == subject_id).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return subject.teachers


@router.post("/{subject_id}/teachers/{teacher_id}", status_code=status.HTTP_201_CREATED)
async def assign_teacher_to_subject(
    subject_id: int,
    teacher_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Assign a teacher to a subject."""
    # Get subject
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Get teacher
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Check if already assigned
    if teacher in subject.teachers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher already assigned to this subject"
        )
    
    # Assign teacher
    subject.teachers.append(teacher)
    db.commit()
    
    return {"message": "Teacher successfully assigned to subject"}


@router.delete("/{subject_id}/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_teacher_from_subject(
    subject_id: int,
    teacher_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a teacher from a subject."""
    # Get subject
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Get teacher
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Check if assigned
    if teacher not in subject.teachers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher not assigned to this subject"
        )
    
    # Remove teacher
    subject.teachers.remove(teacher)
    db.commit()


# ============================================================================
# STATISTICS AND UTILITY ENDPOINTS
# ============================================================================

@router.get("/stats/summary")
async def get_subjects_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get subjects statistics summary."""
    
    # Basic counts
    total_subjects = db.query(Subject).count()
    
    # By type
    type_stats = db.query(
        Subject.type_matiere,
        func.count(Subject.id).label('count')
    ).group_by(Subject.type_matiere).all()
    
    # By level (approximation)
    level_stats = db.query(
        Subject.niveau_requis,
        func.count(Subject.id).label('count')
    ).group_by(Subject.niveau_requis).all()
    
    # Hours statistics
    hours_stats = db.query(
        func.min(Subject.heures_semaine).label('min_hours'),
        func.max(Subject.heures_semaine).label('max_hours'),
        func.avg(Subject.heures_semaine).label('avg_hours')
    ).first()
    
    # Subjects with/without teachers
    subjects_with_teachers = db.query(Subject).join(Subject.teachers).distinct().count()
    subjects_without_teachers = total_subjects - subjects_with_teachers
    
    return {
        "total_subjects": total_subjects,
        "by_type": {item.type_matiere: item.count for item in type_stats},
        "by_level": {item.niveau_requis: item.count for item in level_stats},
        "hours_statistics": {
            "min_hours": hours_stats.min_hours,
            "max_hours": hours_stats.max_hours,
            "avg_hours": round(float(hours_stats.avg_hours or 0), 2)
        },
        "teacher_assignment": {
            "with_teachers": subjects_with_teachers,
            "without_teachers": subjects_without_teachers
        }
    }


 