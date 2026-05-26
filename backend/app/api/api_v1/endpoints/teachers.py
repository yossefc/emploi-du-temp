"""CRUD Teacher (avec gestion de qualified_subjects)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.api.api_v1.endpoints._crud import build_crud_router
from app.models import Subject, Teacher
from app.schemas import TeacherCreate, TeacherRead, TeacherUpdate


def _apply_qualifications(teacher: Teacher, payload, db: Session) -> None:
    """Réaffecte qualified_subjects depuis payload.qualified_subject_ids."""
    ids = getattr(payload, "qualified_subject_ids", None)
    if ids is None:
        return
    subjects = db.query(Subject).filter(Subject.id.in_(ids)).all() if ids else []
    teacher.qualified_subjects = subjects


router = build_crud_router(
    model=Teacher,
    create_schema=TeacherCreate,
    update_schema=TeacherUpdate,
    read_schema=TeacherRead,
    entity_label="Enseignant",
)


# Patch TeacherRead pour inclure les qualified_subject_ids dérivés
from fastapi.encoders import jsonable_encoder
from app.schemas import TeacherRead as _TeacherRead


def _teacher_to_read(teacher: Teacher) -> dict:
    base = jsonable_encoder(teacher, exclude={"qualified_subjects"})
    base["qualified_subject_ids"] = [s.id for s in teacher.qualified_subjects]
    return base


# Surcharge des handlers POST / GET / PATCH pour sérialiser les qualifs
from fastapi import Depends, HTTPException
from app.db.base import get_db

# On retire les routes auto-générées pour les remplacer (sinon les ids manquent)
router.routes = [r for r in router.routes if r.path not in {"", "/{item_id}"}]


@router.post("", response_model=_TeacherRead, status_code=201)
def create_teacher(payload: TeacherCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={"qualified_subject_ids"})
    t = Teacher(**data)
    db.add(t)
    db.flush()
    _apply_qualifications(t, payload, db)
    db.commit()
    db.refresh(t)
    return _teacher_to_read(t)


@router.get("/{item_id}", response_model=_TeacherRead)
def get_teacher(item_id: int, db: Session = Depends(get_db)):
    t = db.get(Teacher, item_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Enseignant introuvable")
    return _teacher_to_read(t)


@router.patch("/{item_id}", response_model=_TeacherRead)
def patch_teacher(item_id: int, patch: TeacherUpdate, db: Session = Depends(get_db)):
    t = db.get(Teacher, item_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Enseignant introuvable")
    data = patch.model_dump(exclude_unset=True, exclude={"qualified_subject_ids"})
    for k, v in data.items():
        setattr(t, k, v)
    if patch.qualified_subject_ids is not None:
        _apply_qualifications(t, patch, db)
    db.commit()
    db.refresh(t)
    return _teacher_to_read(t)


# La liste générique n'a pas les qualifs : on la surcharge aussi
from fastapi import Query

@router.get("", response_model=list[_TeacherRead])
def list_teachers(school_id: int = Query(...), db: Session = Depends(get_db)):
    teachers = db.query(Teacher).filter(Teacher.school_id == school_id).order_by(Teacher.id).all()
    return [_teacher_to_read(t) for t in teachers]
