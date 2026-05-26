"""Contraintes de BLOCAGE de créneaux (HARD relaxables).

Bloque un (day, slot) ou une liste de slots pour :
- L'école entière (BLOCK_SLOT_SCHOOL) — ex: prière, cérémonie
- Une classe spécifique (BLOCK_SLOT_CLASS) — ex: sortie scolaire
- Un Group spécifique (BLOCK_SLOT_GROUP) — ex: groupe en stage
- Un prof (BLOCK_SLOT_TEACHER) — indisponibilité
- Une salle (BLOCK_SLOT_ROOM) — travaux, réservation

Toutes utilisent une assomption littérale pour permettre l'extraction MUS.

Format des `parameters` JSON :
{
    "day_of_week": int,                 # 0-6, OU "days": [int, ...]
    "slot_indices": [int, ...],         # créneaux bloqués ce(s) jour(s)
    "target_id": int                    # FK selon le type (teacher_id, class_id, ...)
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.models import ConstraintPriority
from app.solver.constraints.base import BaseConstraint, ConstraintExplanation

if TYPE_CHECKING:
    from app.solver.context import SolverContext


def _positions_from_params(params: dict) -> list[tuple[int, int]]:
    """Extrait la liste de (day, slot) bloqués depuis le JSON params."""
    days = params.get("days") or ([params["day_of_week"]] if "day_of_week" in params else [])
    slots = params.get("slot_indices", [])
    return [(d, s) for d in days for s in slots]


class _BlockSlotBase(BaseConstraint):
    """Helper : ajoute une assomption + interdit les groups concernés à ces positions."""

    def __init__(
        self,
        *,
        positions: list[tuple[int, int]],
        target_id: Optional[int],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.positions = positions
        self.target_id = target_id

    def _target_groups(self, ctx: "SolverContext") -> list[int]:
        """À surcharger : liste des group_ids touchés par ce blocage."""
        raise NotImplementedError

    def apply(self, ctx: "SolverContext") -> None:
        group_ids = self._target_groups(ctx)
        if not group_ids or not self.positions:
            return

        # Créer une assomption (1 = contrainte active). Si infaisable, le solveur
        # remontera ce literal dans le MUS.
        lit = ctx.model.NewBoolVar(f"assum_{self.constraint_type}_{self.db_id or 'sys'}")
        self.assumption_literal = lit

        for day, slot in self.positions:
            for g_id in group_ids:
                var = ctx.assigned[g_id].get((day, slot))
                if var is None:
                    continue
                # var == 0 quand lit == 1 (contrainte active)
                ctx.model.Add(var == 0).OnlyEnforceIf(lit)

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            positions=_positions_from_params(params),
            target_id=params.get("target_id"),
            db_id=db_id,
            priority=priority,
            weight=weight,
            origin_description=origin_description,
        )

    @classmethod
    def parameters_schema(cls) -> dict:
        return {
            "type": "object",
            "properties": {
                "days": {"type": "array", "items": {"type": "integer", "minimum": 0, "maximum": 6}},
                "day_of_week": {"type": "integer", "minimum": 0, "maximum": 6},
                "slot_indices": {"type": "array", "items": {"type": "integer", "minimum": 0}},
                "target_id": {"type": "integer"},
            },
            "required": ["slot_indices"],
        }


class BlockSlotSchoolConstraint(_BlockSlotBase):
    constraint_type = "block_slot_school"

    def _target_groups(self, ctx):
        return [g.id for g in ctx.groups]

    def explain(self, ctx, lang="fr"):
        slots_str = ", ".join(f"jour {d} créneau {s}" for d, s in self.positions)
        return ConstraintExplanation(
            title="École fermée",
            detail=f"Aucun cours autorisé sur {slots_str}.",
            origin=self.origin_description or "Admin école",
        )


class BlockSlotClassConstraint(_BlockSlotBase):
    constraint_type = "block_slot_class"

    def _target_groups(self, ctx):
        if self.target_id is None:
            return []
        return ctx.groups_of_class(self.target_id)

    def explain(self, ctx, lang="fr"):
        slots_str = ", ".join(f"jour {d} créneau {s}" for d, s in self.positions)
        return ConstraintExplanation(
            title=f"Classe #{self.target_id} indisponible",
            detail=f"La classe ne peut suivre aucun cours sur {slots_str}.",
            origin=self.origin_description or "Admin école",
        )


class BlockSlotGroupConstraint(_BlockSlotBase):
    constraint_type = "block_slot_group"

    def _target_groups(self, ctx):
        return [self.target_id] if self.target_id is not None else []

    def explain(self, ctx, lang="fr"):
        slots_str = ", ".join(f"jour {d} créneau {s}" for d, s in self.positions)
        return ConstraintExplanation(
            title=f"Groupe #{self.target_id} indisponible",
            detail=f"Ce groupe ne peut pas être placé sur {slots_str}.",
            origin=self.origin_description or "Admin école",
        )


class BlockSlotTeacherConstraint(_BlockSlotBase):
    constraint_type = "block_slot_teacher"

    def _target_groups(self, ctx):
        if self.target_id is None:
            return []
        return ctx.groups_of_teacher(self.target_id)

    def explain(self, ctx, lang="fr"):
        try:
            t = ctx.teacher(self.target_id) if self.target_id else None
            who = t.full_name if t else f"Prof #{self.target_id}"
        except KeyError:
            who = f"Prof #{self.target_id}"
        slots_str = ", ".join(f"jour {d} créneau {s}" for d, s in self.positions)
        return ConstraintExplanation(
            title=f"Indisponibilité {who}",
            detail=f"{who} ne peut pas enseigner sur {slots_str}.",
            origin=self.origin_description or "Admin école",
        )


class BlockSlotRoomConstraint(_BlockSlotBase):
    """Bloque l'utilisation d'une salle sur certains créneaux.

    Sémantique : aucun Group ne peut utiliser cette room sur ces (day, slot).
    Implémenté différemment des autres : on contraint `room_used[g][s][room_id] == 0`.
    """
    constraint_type = "block_slot_room"

    def _target_groups(self, ctx):
        # Overridé : on n'utilise pas le mécanisme générique
        return []

    def apply(self, ctx: "SolverContext") -> None:
        if self.target_id is None or not self.positions:
            return
        room_id = self.target_id
        lit = ctx.model.NewBoolVar(f"assum_{self.constraint_type}_{self.db_id or 'sys'}")
        self.assumption_literal = lit
        for day, slot in self.positions:
            for g_id, slot_map in ctx.room_used.items():
                slot_vars = slot_map.get((day, slot), {})
                if room_id in slot_vars:
                    ctx.model.Add(slot_vars[room_id] == 0).OnlyEnforceIf(lit)

    def explain(self, ctx, lang="fr"):
        r = ctx.room(self.target_id) if self.target_id else None
        who = r.name if r else f"Salle #{self.target_id}"
        slots_str = ", ".join(f"jour {d} créneau {s}" for d, s in self.positions)
        return ConstraintExplanation(
            title=f"Salle indisponible : {who}",
            detail=f"La salle {who} n'est pas utilisable sur {slots_str}.",
            origin=self.origin_description or "Admin école",
        )
