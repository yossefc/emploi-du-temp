"""Endpoints CRUD pour School + sa grille horaire (TimeSlot bulk).

POST   /schools                    create
GET    /schools                    list (toutes — école = tenant racine)
GET    /schools/{id}               read
PATCH  /schools/{id}               update
DELETE /schools/{id}               delete

POST   /schools/{id}/time-grid     replace whole grid (atomic)
GET    /schools/{id}/time-grid     read whole grid
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.api_v1.endpoints._crud import build_crud_router
from app.db.base import get_db
from app.models import School, TimeSlot
from app.schemas import (
    SchoolCreate,
    SchoolRead,
    SchoolUpdate,
    TimeGridReplace,
    TimeSlotRead,
)


router = build_crud_router(
    model=School,
    create_schema=SchoolCreate,
    update_schema=SchoolUpdate,
    read_schema=SchoolRead,
    entity_label="École",
    require_school_id_for_list=False,
)


@router.post("/{school_id}/time-grid", response_model=list[TimeSlotRead])
def replace_time_grid(
    school_id: int,
    payload: TimeGridReplace,
    db: Session = Depends(get_db),
):
    """Remplace TOUTE la grille horaire de l'école par celle fournie (atomique)."""
    if db.get(School, school_id) is None:
        raise HTTPException(status_code=404, detail="École introuvable")

    db.query(TimeSlot).filter(TimeSlot.school_id == school_id).delete(synchronize_session=False)

    new_slots = []
    for slot in payload.slots:
        ts = TimeSlot(school_id=school_id, **slot.model_dump())
        db.add(ts)
        new_slots.append(ts)
    db.commit()
    for ts in new_slots:
        db.refresh(ts)
    return new_slots


@router.get("/{school_id}/time-grid", response_model=list[TimeSlotRead])
def get_time_grid(school_id: int, db: Session = Depends(get_db)):
    if db.get(School, school_id) is None:
        raise HTTPException(status_code=404, detail="École introuvable")
    return (
        db.query(TimeSlot)
        .filter(TimeSlot.school_id == school_id)
        .order_by(TimeSlot.day_of_week, TimeSlot.slot_index)
        .all()
    )
