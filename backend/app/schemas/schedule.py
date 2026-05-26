"""Pydantic schemas pour les plannings et la génération."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import ScheduleStatus


# ---------------------------------------------------------------------------
# Lecture de plannings existants
# ---------------------------------------------------------------------------

class ScheduleEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    room_id: Optional[int]
    day_of_week: int
    slot_index: int


class ScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    name: str
    status: ScheduleStatus
    generated_at: Optional[datetime] = None
    generator_user_id: Optional[int] = None
    relaxed_constraints_report: Optional[dict] = None
    quality_score: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ScheduleWithEntries(ScheduleRead):
    entries: list[ScheduleEntryRead] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Génération + dialogue conflit
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    """Body de POST /schedules/generate."""
    school_id: int
    name: str = Field(default="Planning généré", max_length=200)
    disabled_constraint_ids: list[int] = Field(
        default_factory=list,
        description="IDs des contraintes DB à désactiver pour cette tentative (résolution conflit)",
    )
    max_time_seconds: float = Field(default=30.0, ge=1.0, le=300.0)


class ConflictSuggestion(BaseModel):
    """Suggestion d'action concrète pour résoudre un conflit."""
    kind: str
    title_he: str
    title_fr: str
    description_he: str
    description_fr: str
    # Action automatique optionnelle (1-clic depuis l'UI)
    auto_action: Optional[dict] = None


class ConstraintConflictInfo(BaseModel):
    """Une entrée du MUS — contrainte identifiée comme cause de l'infaisabilité.

    Tous les textes sont fournis bilingue (FR + HE).
    """
    constraint_id: Optional[int] = Field(
        None, description="ID DB de la contrainte (null si contrainte système implicite)"
    )
    constraint_type: str
    title_he: str
    title_fr: str
    detail_he: str
    detail_fr: str
    origin: str
    suggestions: list[ConflictSuggestion] = Field(default_factory=list)


class GenerateResponseSuccess(BaseModel):
    success: bool = True
    schedule_id: int
    placed_entries: int
    relaxed_constraint_ids: list[int] = Field(default_factory=list)
    solver_time_seconds: float


class GenerateResponseConflict(BaseModel):
    success: bool = False
    conflicts: list[ConstraintConflictInfo]
    solver_time_seconds: float
    message: str = (
        "Conflit détecté entre plusieurs contraintes. "
        "Choisissez celles à relaxer puis relancez la génération."
    )


class GenerateResponseTimeout(BaseModel):
    success: bool = False
    timeout: bool = True
    solver_time_seconds: float
    message: str = (
        "Le solveur n'a pas trouvé de solution dans le temps imparti. "
        "Augmentez max_time_seconds ou simplifiez les contraintes."
    )
