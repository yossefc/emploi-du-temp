"""CRUD Group + ParallelCohort (avec M2M teachers + source_classes)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models import Class, Group, ParallelCohort, Teacher
from app.schemas import (
    GroupCreate,
    GroupRead,
    GroupUpdate,
    ParallelCohortCreate,
    ParallelCohortRead,
    ParallelCohortUpdate,
)


router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers de sérialisation (inject les *_ids dérivés du M2M)
# ---------------------------------------------------------------------------

def _group_to_read(g: Group) -> dict:
    return {
        "id": g.id,
        "school_id": g.school_id,
        "grade_id": g.grade_id,
        "subject_id": g.subject_id,
        "label": g.label,
        "group_type": g.group_type,
        "hours_per_week": g.hours_per_week,
        "student_count": g.student_count,
        "parallel_cohort_id": g.parallel_cohort_id,
        "teacher_ids": [t.id for t in g.teachers],
        "source_class_ids": [c.id for c in g.source_classes],
        "created_at": g.created_at,
        "updated_at": g.updated_at,
    }


def _cohort_to_read(c: ParallelCohort) -> dict:
    return {
        "id": c.id,
        "school_id": c.school_id,
        "grade_id": c.grade_id,
        "label": c.label,
        "group_ids": [g.id for g in c.groups],
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


def _apply_group_m2m(g: Group, *, teacher_ids: list[int] | None, source_class_ids: list[int] | None, db: Session):
    if teacher_ids is not None:
        g.teachers = db.query(Teacher).filter(Teacher.id.in_(teacher_ids)).all() if teacher_ids else []
    if source_class_ids is not None:
        g.source_classes = db.query(Class).filter(Class.id.in_(source_class_ids)).all() if source_class_ids else []


# ---------------------------------------------------------------------------
# Groups CRUD
# ---------------------------------------------------------------------------

@router.post("/groups", response_model=GroupRead, status_code=status.HTTP_201_CREATED, tags=["groups"])
def create_group(payload: GroupCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={"teacher_ids", "source_class_ids"})
    g = Group(**data)
    db.add(g)
    db.flush()
    _apply_group_m2m(g, teacher_ids=payload.teacher_ids, source_class_ids=payload.source_class_ids, db=db)
    db.commit()
    db.refresh(g)
    return _group_to_read(g)


@router.get("/groups", response_model=list[GroupRead], tags=["groups"])
def list_groups(
    school_id: int = Query(...),
    grade_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Group).filter(Group.school_id == school_id)
    if grade_id is not None:
        q = q.filter(Group.grade_id == grade_id)
    return [_group_to_read(g) for g in q.order_by(Group.id).all()]


@router.get("/groups/{group_id}", response_model=GroupRead, tags=["groups"])
def get_group(group_id: int, db: Session = Depends(get_db)):
    g = db.get(Group, group_id)
    if g is None:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    return _group_to_read(g)


@router.patch("/groups/{group_id}", response_model=GroupRead, tags=["groups"])
def patch_group(group_id: int, patch: GroupUpdate, db: Session = Depends(get_db)):
    g = db.get(Group, group_id)
    if g is None:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    data = patch.model_dump(exclude_unset=True, exclude={"teacher_ids", "source_class_ids"})
    for k, v in data.items():
        setattr(g, k, v)
    _apply_group_m2m(g, teacher_ids=patch.teacher_ids, source_class_ids=patch.source_class_ids, db=db)
    db.commit()
    db.refresh(g)
    return _group_to_read(g)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["groups"])
def delete_group(group_id: int, db: Session = Depends(get_db)):
    g = db.get(Group, group_id)
    if g is None:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    db.delete(g)
    db.commit()


# ---------------------------------------------------------------------------
# ParallelCohorts CRUD
# ---------------------------------------------------------------------------

@router.post("/cohorts", response_model=ParallelCohortRead, status_code=status.HTTP_201_CREATED, tags=["cohorts"])
def create_cohort(payload: ParallelCohortCreate, db: Session = Depends(get_db)):
    c = ParallelCohort(**payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return _cohort_to_read(c)


@router.get("/cohorts", response_model=list[ParallelCohortRead], tags=["cohorts"])
def list_cohorts(school_id: int = Query(...), db: Session = Depends(get_db)):
    return [
        _cohort_to_read(c)
        for c in db.query(ParallelCohort).filter(ParallelCohort.school_id == school_id).order_by(ParallelCohort.id).all()
    ]


@router.get("/cohorts/{cohort_id}", response_model=ParallelCohortRead, tags=["cohorts"])
def get_cohort(cohort_id: int, db: Session = Depends(get_db)):
    c = db.get(ParallelCohort, cohort_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Cohorte introuvable")
    return _cohort_to_read(c)


@router.patch("/cohorts/{cohort_id}", response_model=ParallelCohortRead, tags=["cohorts"])
def patch_cohort(cohort_id: int, patch: ParallelCohortUpdate, db: Session = Depends(get_db)):
    c = db.get(ParallelCohort, cohort_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Cohorte introuvable")
    for k, v in patch.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return _cohort_to_read(c)


@router.delete("/cohorts/{cohort_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["cohorts"])
def delete_cohort(cohort_id: int, db: Session = Depends(get_db)):
    c = db.get(ParallelCohort, cohort_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Cohorte introuvable")
    db.delete(c)
    db.commit()
