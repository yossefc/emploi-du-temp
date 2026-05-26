"""Helper minimaliste pour générer un CRUD scopé par école.

Au lieu de TypeVar génériques (qui posent problème avec pydantic ForwardRef),
on génère les routes en construisant dynamiquement les annotations.
"""

from __future__ import annotations

from typing import Optional, Type

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base import Base, get_db


def build_crud_router(
    *,
    model: Type[Base],
    create_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    read_schema: Type[BaseModel],
    entity_label: str,
    require_school_id_for_list: bool = True,
) -> APIRouter:
    """Construit un router CRUD standard, sans M2M (utiliser des endpoints
    explicites pour les modèles avec relations many-to-many).
    """
    router = APIRouter()

    def _create(payload, db: Session = Depends(get_db)):
        obj = model(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    _create.__annotations__["payload"] = create_schema

    def _list(
        school_id: Optional[int] = Query(None),
        db: Session = Depends(get_db),
    ):
        q = db.query(model)
        if hasattr(model, "school_id"):
            if school_id is None and require_school_id_for_list:
                raise HTTPException(400, "school_id est obligatoire pour cette entité")
            if school_id is not None:
                q = q.filter(model.school_id == school_id)
        return q.order_by(model.id).all()

    def _get(item_id: int, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(404, f"{entity_label} introuvable")
        return obj

    def _patch(item_id: int, patch, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(404, f"{entity_label} introuvable")
        for k, v in patch.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj
    _patch.__annotations__["patch"] = update_schema

    def _delete(item_id: int, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(404, f"{entity_label} introuvable")
        db.delete(obj)
        db.commit()

    router.add_api_route("", _create, methods=["POST"], response_model=read_schema,
                          status_code=status.HTTP_201_CREATED)
    router.add_api_route("", _list, methods=["GET"], response_model=list[read_schema])
    router.add_api_route("/{item_id}", _get, methods=["GET"], response_model=read_schema)
    router.add_api_route("/{item_id}", _patch, methods=["PATCH"], response_model=read_schema)
    router.add_api_route("/{item_id}", _delete, methods=["DELETE"],
                          status_code=status.HTTP_204_NO_CONTENT)
    return router
