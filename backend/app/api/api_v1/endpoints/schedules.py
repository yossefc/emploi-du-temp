"""Endpoints planning : génération + dialogue conflit + lecture.

POST   /schedules/generate              — lance le solveur, retourne succès | conflit | timeout
GET    /schedules                       — liste pour une école
GET    /schedules/{id}                  — détail (avec entries)
POST   /schedules/{id}/accept           — DRAFT → ACTIVE (toutes les autres ACTIVE deviennent ARCHIVED)
DELETE /schedules/{id}                  — supprime un brouillon
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models import Schedule, ScheduleStatus
from app.schemas import (
    ConstraintConflictInfo,
    GenerateRequest,
    GenerateResponseConflict,
    GenerateResponseSuccess,
    GenerateResponseTimeout,
    ScheduleRead,
    ScheduleWithEntries,
)
from app.solver import (
    SolveConflict,
    SolveSuccess,
    SolveTimeout,
    TimetableEngine,
)


router = APIRouter()


@router.post(
    "/generate",
    response_model=None,
    summary="Lance la génération d'un planning",
    description=(
        "Renvoie soit un succès (`success=true` + schedule_id), soit un conflit "
        "(`success=false` + liste des contraintes en conflit), soit un timeout."
    ),
)
def generate_schedule(req: GenerateRequest, db: Session = Depends(get_db)):
    engine = TimetableEngine(db, req.school_id)
    result = engine.generate(
        schedule_name=req.name,
        disabled_constraint_ids=req.disabled_constraint_ids,
        max_time_seconds=req.max_time_seconds,
    )

    if isinstance(result, SolveSuccess):
        return GenerateResponseSuccess(
            schedule_id=result.schedule_id,
            placed_entries=result.placed_entries,
            relaxed_constraint_ids=result.relaxed_constraint_ids,
            solver_time_seconds=result.solver_time_seconds,
        )

    if isinstance(result, SolveConflict):
        return GenerateResponseConflict(
            conflicts=[
                ConstraintConflictInfo(
                    constraint_id=c.constraint_id,
                    constraint_type=c.constraint_type,
                    title=c.explanation.title,
                    detail=c.explanation.detail,
                    origin=c.explanation.origin,
                )
                for c in result.conflicts
            ],
            solver_time_seconds=result.solver_time_seconds,
        )

    # Timeout
    return GenerateResponseTimeout(solver_time_seconds=result.solver_time_seconds)


@router.get("", response_model=list[ScheduleRead])
def list_schedules(
    school_id: int = Query(..., description="Filtrer par école"),
    status: ScheduleStatus | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Schedule).filter(Schedule.school_id == school_id)
    if status is not None:
        q = q.filter(Schedule.status == status)
    return q.order_by(Schedule.created_at.desc()).all()


@router.get("/{schedule_id}", response_model=ScheduleWithEntries)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    sched = db.get(Schedule, schedule_id)
    if sched is None:
        raise HTTPException(status_code=404, detail="Planning introuvable")
    return sched


@router.post("/{schedule_id}/accept", response_model=ScheduleRead)
def accept_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Promeut un DRAFT en ACTIVE. Les autres ACTIVE de la même école sont ARCHIVED."""
    sched = db.get(Schedule, schedule_id)
    if sched is None:
        raise HTTPException(status_code=404, detail="Planning introuvable")
    if sched.status != ScheduleStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Le planning est en statut {sched.status.value}, seuls les DRAFT peuvent être acceptés.",
        )

    # Archiver les anciens ACTIVE de cette école
    db.query(Schedule).filter(
        Schedule.school_id == sched.school_id,
        Schedule.status == ScheduleStatus.ACTIVE,
    ).update({Schedule.status: ScheduleStatus.ARCHIVED}, synchronize_session=False)

    sched.status = ScheduleStatus.ACTIVE
    db.commit()
    db.refresh(sched)
    return sched


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    sched = db.get(Schedule, schedule_id)
    if sched is None:
        raise HTTPException(status_code=404, detail="Planning introuvable")
    if sched.status == ScheduleStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Impossible de supprimer un planning ACTIVE. Acceptez-en un autre d'abord.",
        )
    db.delete(sched)
    db.commit()
