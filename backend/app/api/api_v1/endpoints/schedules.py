"""
Schedule management endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from celery import Celery

from app.core.auth import get_current_active_user, require_admin
from app.db.base import get_db
from app.models import User, Schedule, ScheduleEntry
from app.schemas.schedule import (
    ScheduleResponse as ScheduleSchema,
    ScheduleCreate,
    ScheduleUpdate,
    GenerateScheduleRequest,
    GenerateScheduleResponse,
    ScheduleEntryResponse as ScheduleEntrySchema
)
from app.solver.timetable_solver import TimetableSolver
from app.core.config import settings

router = APIRouter()

# Initialize Celery
celery_app = Celery(
    'tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)


@router.get("/", response_model=List[ScheduleSchema])
async def get_schedules(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all schedules."""
    schedules = db.query(Schedule).offset(skip).limit(limit).all()
    return schedules


@router.get("/{schedule_id}", response_model=ScheduleSchema)
async def get_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific schedule."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.post("/generate", response_model=GenerateScheduleResponse)
async def generate_schedule(
    request: GenerateScheduleRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Generate a new schedule using the solver."""
    # Create schedule record
    schedule = Schedule(
        name=request.name,
        description=request.description,
        academic_year=request.academic_year,
        semester=request.semester,
        status="draft",
        created_by_id=current_user.id
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    # Start generation task
    background_tasks.add_task(
        generate_schedule_task,
        schedule_id=schedule.id,
        time_limit=request.time_limit_seconds
    )
    
    return GenerateScheduleResponse(
        schedule_id=schedule.id,
        status="pending",
        generation_time=0,
        entries_count=0,
        conflicts_count=0,
        message="Schedule generation started. Check status for progress."
    )


def generate_schedule_task(schedule_id: int, time_limit: int = None):
    """Background task to generate schedule."""
    from app.db.base import SessionLocal
    
    db = SessionLocal()
    try:
        # Get schedule
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            return
        
        # Initialize solver
        solver = TimetableSolver(db)
        solver.build_model()
        
        # Solve
        result = solver.solve(time_limit_seconds=time_limit)
        
        # Update schedule with results
        schedule.solver_status = result['status']
        schedule.generation_time_seconds = result['solution_time']
        schedule.objective_value = result.get('objective_value')
        
        if result['status'] in ['optimal', 'feasible']:
            # Save assignments
            for assignment in result['assignments']:
                entry = ScheduleEntry(
                    schedule_id=schedule_id,
                    day_of_week=assignment['day'],
                    period=assignment['period'],
                    class_group_id=assignment['class_id'],
                    subject_id=assignment['subject_id'],
                    teacher_id=assignment['teacher_id'],
                    room_id=assignment['room_id']
                )
                db.add(entry)
            
            schedule.status = 'active' if result['status'] == 'optimal' else 'draft'
        else:
            schedule.status = 'draft'
            schedule.conflicts_json = result.get('conflicts', [])
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        if schedule:
            schedule.status = 'draft'
            schedule.conflicts_json = [{"type": "error", "description": str(e)}]
            db.commit()
    finally:
        db.close()


@router.put("/{schedule_id}", response_model=ScheduleSchema)
async def update_schedule(
    schedule_id: int,
    schedule_update: ScheduleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a schedule."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    update_data = schedule_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a schedule."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted successfully"}


@router.get("/{schedule_id}/entries", response_model=List[ScheduleEntrySchema])
async def get_schedule_entries(
    schedule_id: int,
    day_of_week: int = None,
    class_group_id: int = None,
    teacher_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get schedule entries with optional filters."""
    query = db.query(ScheduleEntry).filter(ScheduleEntry.schedule_id == schedule_id)
    
    if day_of_week is not None:
        query = query.filter(ScheduleEntry.day_of_week == day_of_week)
    if class_group_id is not None:
        query = query.filter(ScheduleEntry.class_group_id == class_group_id)
    if teacher_id is not None:
        query = query.filter(ScheduleEntry.teacher_id == teacher_id)
    
    entries = query.all()
    return entries


@router.post("/{schedule_id}/clone", response_model=ScheduleSchema)
async def clone_schedule(
    schedule_id: int,
    new_name: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Clone an existing schedule."""
    # Get original schedule
    original = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Create new schedule
    new_schedule = Schedule(
        name=new_name,
        description=f"Cloned from {original.name}",
        academic_year=original.academic_year,
        semester=original.semester,
        status="draft",
        parent_schedule_id=original.id,
        version=original.version + 1,
        created_by_id=current_user.id
    )
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    
    # Clone entries
    for entry in original.entries:
        new_entry = ScheduleEntry(
            schedule_id=new_schedule.id,
            day_of_week=entry.day_of_week,
            period=entry.period,
            class_group_id=entry.class_group_id,
            subject_id=entry.subject_id,
            teacher_id=entry.teacher_id,
            room_id=entry.room_id,
            is_double_period=entry.is_double_period,
            notes=entry.notes,
            is_locked=entry.is_locked
        )
        db.add(new_entry)
    
    db.commit()
    db.refresh(new_schedule)
    
    return new_schedule 