"""BaseConstraint — interface commune à toutes les contraintes du solveur.

Chaque contrainte concrète implémente trois choses :
1. `apply(ctx)` : ajoute la règle au modèle CP-SAT (avec assomption littérale si HARD relaxable)
2. `explain(ctx, lang)` : produit l'explication humaine pour le dialogue conflit
3. `from_db(constraint, ...)` : construit l'instance depuis une ligne `constraints` DB

Les contraintes STRUCTURELLES (TEACHER_NO_OVERLAP, etc.) n'ont pas d'origine DB —
elles sont ajoutées en dur par l'engine via des subclasses dédiées.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from app.models import Constraint as DBConstraint
from app.models import ConstraintPriority

if TYPE_CHECKING:
    from app.solver.context import SolverContext


@dataclass
class ConstraintExplanation:
    """Texte d'explication produit pour le dialogue avec l'utilisateur."""
    title: str       # ex: "Indispo Mme Cohen lundi 8h-10h"
    detail: str      # ex: "Mme Cohen est marquée indisponible le lundi de 8h à 10h"
    origin: str      # ex: "Posée par yossef@amit.org le 26/05/2026"


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
        # Rempli par l'engine pendant `apply()` si la contrainte est relaxable
        # (utilisé pour l'extraction MUS via SufficientAssumptionsForInfeasibility)
        self.assumption_literal: Optional[Any] = None

    # ---- Interface ----
    @abstractmethod
    def apply(self, ctx: "SolverContext") -> None:
        """Ajoute cette contrainte au modèle CP-SAT de `ctx`.

        Pour les HARD relaxables : créer une BoolVar d'assomption, la stocker
        dans `self.assumption_literal`, et conditionner la contrainte avec
        `model.Add(...).OnlyEnforceIf(literal)`. L'engine appellera ensuite
        `model.AddAssumption(literal)`.

        Pour les SOFT : ajouter une variable de pénalité à minimiser dans
        l'objectif (l'engine s'occupera de l'objectif global).
        """

    @abstractmethod
    def explain(self, ctx: "SolverContext", lang: str = "fr") -> ConstraintExplanation:
        """Produit l'explication humaine."""

    # ---- Construction depuis la DB ----
    @classmethod
    def from_db(cls, db_constraint: DBConstraint) -> "BaseConstraint":
        """Construit l'instance depuis une ligne `constraints` de la DB.

        La sous-classe lit `db_constraint.parameters` (JSON) selon son schéma.
        """
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

    # ---- Métadonnées schéma (pour validation côté API/UI) ----
    @classmethod
    def parameters_schema(cls) -> dict:
        """JSON-Schema des `parameters` attendus pour ce type de contrainte.

        Utilisé par l'API pour valider la création d'une contrainte, et par
        l'UI pour générer le formulaire de saisie. Override en subclass.
        """
        return {"type": "object"}
