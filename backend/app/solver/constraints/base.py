"""BaseConstraint — interface commune à toutes les contraintes du solveur.

Chaque contrainte concrète implémente :
1. `apply(ctx)` : ajoute la règle au modèle CP-SAT (avec assomption littérale si HARD relaxable)
2. `explain(ctx)` : produit l'explication BILINGUE (FR/HE) + SUGGESTIONS d'action
3. `from_db(constraint, ...)` : construit l'instance depuis une ligne `constraints` DB

Les contraintes STRUCTURELLES (TEACHER_NO_OVERLAP, etc.) n'ont pas d'origine DB —
elles sont ajoutées en dur par l'engine via des subclasses dédiées.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from app.models import Constraint as DBConstraint
from app.models import ConstraintPriority

if TYPE_CHECKING:
    from app.solver.context import SolverContext


@dataclass
class Suggestion:
    """Suggestion d'action concrète pour résoudre un conflit.

    Affichée dans la modal ConflictDialog. Si `auto_action` est fourni,
    un bouton "Appliquer" permet de l'exécuter en 1 clic.
    """
    kind: str                # ex: "disable_constraint", "reduce_group_hours", "add_alternative_teacher"
    title_he: str            # titre court en hébreu
    title_fr: str            # titre court en français
    description_he: str      # explication détaillée HE
    description_fr: str      # explication détaillée FR
    # Si renseigné, l'UI affiche un bouton "Appliquer" qui exécute cette action.
    # Format : {"verb": "patch_constraint" | "patch_group" | "delete_constraint", "target_id": int, "patch"?: dict}
    auto_action: Optional[dict] = None


@dataclass
class ConstraintExplanation:
    """Texte d'explication BILINGUE produit pour le dialogue conflit."""
    title_he: str
    title_fr: str
    detail_he: str
    detail_fr: str
    origin: str                                       # libre, généralement la description posée par l'admin
    suggestions: list[Suggestion] = field(default_factory=list)


class BaseConstraint(ABC):
    """Classe de base abstraite pour toute contrainte modélisable par le solveur.

    Subclasses MUST set `constraint_type` (matching ConstraintType enum).
    """

    constraint_type: str       # défini en subclass — ex: "block_slot_teacher"

    def __init__(
        self,
        *,
        db_id: Optional[int] = None,
        priority: ConstraintPriority = ConstraintPriority.HARD,
        weight: Optional[int] = None,
        origin_description: Optional[str] = None,
    ):
        self.db_id = db_id
        self.priority = priority
        self.weight = weight
        self.origin_description = origin_description
        self.assumption_literal: Optional[Any] = None

    # ---- Interface ----
    @abstractmethod
    def apply(self, ctx: "SolverContext") -> None:
        """Ajoute cette contrainte au modèle CP-SAT de `ctx`."""

    @abstractmethod
    def explain(self, ctx: "SolverContext") -> ConstraintExplanation:
        """Produit l'explication humaine BILINGUE + suggestions de résolution."""

    # ---- Construction depuis la DB ----
    @classmethod
    def from_db(cls, db_constraint: DBConstraint) -> "BaseConstraint":
        return cls._build_from_params(
            params=db_constraint.parameters or {},
            db_id=db_constraint.id,
            priority=db_constraint.priority,
            weight=db_constraint.weight,
            origin_description=db_constraint.origin_description,
        )

    @classmethod
    @abstractmethod
    def _build_from_params(
        cls,
        *,
        params: dict,
        db_id: Optional[int],
        priority: ConstraintPriority,
        weight: Optional[int],
        origin_description: Optional[str],
    ) -> "BaseConstraint":
        """Hook subclass : convertit le JSON params en arguments du constructeur."""

    @classmethod
    def parameters_schema(cls) -> dict:
        return {"type": "object"}


# ---------------------------------------------------------------------------
# Helpers communs pour les explanations
# ---------------------------------------------------------------------------

DAYS_HE = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
DAYS_FR = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]


def humanize_positions_he(positions: list[tuple[int, int]]) -> str:
    """Convertit une liste de (jour, créneau) en phrase lisible HE.

    Si trop nombreux, résume ("X cr�neaux sur Y jours"). Sinon liste joliment.
    """
    if not positions:
        return "—"
    n = len(positions)
    days_used = sorted({d for d, _ in positions})
    if n > 8:
        return f"{n} משבצות זמן ({len(days_used)} ימים)"
    if len(days_used) == 1:
        slots = sorted({s for _, s in positions})
        return f"יום {DAYS_HE[days_used[0]]} (משבצות {', '.join(str(s + 1) for s in slots)})"
    # Quelques positions
    by_day: dict[int, list[int]] = {}
    for d, s in positions:
        by_day.setdefault(d, []).append(s + 1)
    parts = [f"{DAYS_HE[d]} ({','.join(str(s) for s in sorted(slots))})" for d, slots in sorted(by_day.items())]
    return " · ".join(parts)


def humanize_positions_fr(positions: list[tuple[int, int]]) -> str:
    """Version française."""
    if not positions:
        return "—"
    n = len(positions)
    days_used = sorted({d for d, _ in positions})
    if n > 8:
        return f"{n} créneaux sur {len(days_used)} jour(s)"
    if len(days_used) == 1:
        slots = sorted({s for _, s in positions})
        return f"{DAYS_FR[days_used[0]]} (créneaux {', '.join(str(s + 1) for s in slots)})"
    by_day: dict[int, list[int]] = {}
    for d, s in positions:
        by_day.setdefault(d, []).append(s + 1)
    parts = [f"{DAYS_FR[d]} ({','.join(str(s) for s in sorted(slots))})" for d, slots in sorted(by_day.items())]
    return " · ".join(parts)
