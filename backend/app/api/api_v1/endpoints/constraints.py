"""Endpoints CRUD pour les contraintes.

CRUD complet — indispensable pour le dialogue de résolution de conflit :
le user peut désactiver une contrainte (PATCH is_active=False), la modifier,
ou la supprimer après avoir vu qu'elle bloque la génération.

POST   /constraints                — créer
GET    /constraints                — lister (filtrable par school_id, is_active, type)
GET    /constraints/{id}           — détail
PATCH  /constraints/{id}           — modifier (priorité, params, is_active, …)
DELETE /constraints/{id}           — supprimer
GET    /constraints/types/schema   — JSON-Schema des params attendus par type (pour formulaires UI)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models import Constraint, ConstraintType
from app.schemas import ConstraintCreate, ConstraintRead, ConstraintUpdate
from app.solver.constraints import CONSTRAINT_REGISTRY


router = APIRouter()


@router.post("", response_model=ConstraintRead, status_code=201)
def create_constraint(payload: ConstraintCreate, db: Session = Depends(get_db)):
    obj = Constraint(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=list[ConstraintRead])
def list_constraints(
    school_id: int = Query(..., description="Filtrer par école (obligatoire)"),
    is_active: bool | None = Query(None),
    constraint_type: ConstraintType | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Constraint).filter(Constraint.school_id == school_id)
    if is_active is not None:
        q = q.filter(Constraint.is_active == is_active)
    if constraint_type is not None:
        q = q.filter(Constraint.constraint_type == constraint_type)
    return q.order_by(Constraint.id).all()


@router.get("/types/schema")
def list_constraint_types_schema():
    """Renvoie pour chaque type de contrainte son JSON-Schema params.

    Utilisé par l'UI pour générer dynamiquement les formulaires de saisie.
    """
    out = {}
    for ctype_value, cls in CONSTRAINT_REGISTRY.items():
        out[ctype_value] = {
            "class_name": cls.__name__,
            "parameters_schema": cls.parameters_schema(),
        }
    return out


@router.get("/{constraint_id}", response_model=ConstraintRead)
def get_constraint(constraint_id: int, db: Session = Depends(get_db)):
    obj = db.get(Constraint, constraint_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Contrainte introuvable")
    return obj


@router.patch("/{constraint_id}", response_model=ConstraintRead)
def update_constraint(
    constraint_id: int,
    patch: ConstraintUpdate,
    db: Session = Depends(get_db),
):
    obj = db.get(Constraint, constraint_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Contrainte introuvable")
    data = patch.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{constraint_id}", status_code=204)
def delete_constraint(constraint_id: int, db: Session = Depends(get_db)):
    obj = db.get(Constraint, constraint_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Contrainte introuvable")
    db.delete(obj)
    db.commit()
