"""Contraintes de BLOCAGE de créneaux (HARD relaxables) — bilingues + suggestions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.solver.constraints.base import (
    BaseConstraint,
    ConstraintExplanation,
    Suggestion,
    humanize_positions_fr,
    humanize_positions_he,
)

if TYPE_CHECKING:
    from app.solver.context import SolverContext


def _positions_from_params(params: dict) -> list[tuple[int, int]]:
    days = params.get("days") or ([params["day_of_week"]] if "day_of_week" in params else [])
    slots = params.get("slot_indices", [])
    return [(d, s) for d in days for s in slots]


def _disable_self_suggestion(constraint_id: Optional[int], title_he: str, title_fr: str) -> Optional[Suggestion]:
    if constraint_id is None:
        return None
    return Suggestion(
        kind="disable_constraint",
        title_he=f"בטל את האילוץ \"{title_he}\"",
        title_fr=f"Désactiver la contrainte « {title_fr} »",
        description_he="האילוץ יישאר במאגר אך לא ייעשה בו שימוש בייצור הבא.",
        description_fr="La contrainte reste en base mais ne sera plus appliquée lors des générations suivantes.",
        auto_action={"verb": "patch_constraint", "target_id": constraint_id, "patch": {"is_active": False}},
    )


class _BlockSlotBase(BaseConstraint):
    def __init__(self, *, positions: list[tuple[int, int]], target_id: Optional[int], **kwargs):
        super().__init__(**kwargs)
        self.positions = positions
        self.target_id = target_id

    def _target_groups(self, ctx: "SolverContext") -> list[int]:
        raise NotImplementedError

    def apply(self, ctx: "SolverContext") -> None:
        group_ids = self._target_groups(ctx)
        if not group_ids or not self.positions:
            return
        lit = ctx.model.NewBoolVar(f"assum_{self.constraint_type}_{self.db_id or 'sys'}")
        self.assumption_literal = lit
        for day, slot in self.positions:
            for g_id in group_ids:
                var = ctx.assigned[g_id].get((day, slot))
                if var is None:
                    continue
                ctx.model.Add(var == 0).OnlyEnforceIf(lit)

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            positions=_positions_from_params(params),
            target_id=params.get("target_id"),
            db_id=db_id, priority=priority, weight=weight,
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

    def explain(self, ctx):
        he = humanize_positions_he(self.positions)
        fr = humanize_positions_fr(self.positions)
        sug = _disable_self_suggestion(self.db_id, "סגירת בית ספר", "Fermeture école")
        return ConstraintExplanation(
            title_he="סגירת בית הספר",
            title_fr="École fermée",
            detail_he=f"אין שיעורים ב{he}.",
            detail_fr=f"Aucun cours sur {fr}.",
            origin=self.origin_description or "מנהל",
            suggestions=[s for s in [sug] if s],
        )


class BlockSlotClassConstraint(_BlockSlotBase):
    constraint_type = "block_slot_class"

    def _target_groups(self, ctx):
        return ctx.groups_of_class(self.target_id) if self.target_id else []

    def explain(self, ctx):
        cls_label = f"#{self.target_id}"
        try:
            cls = next((c for c in ctx.classes if c.id == self.target_id), None)
            if cls:
                cls_label = cls.code
        except Exception:
            pass
        he = humanize_positions_he(self.positions)
        fr = humanize_positions_fr(self.positions)
        sug = _disable_self_suggestion(self.db_id, f"כיתה {cls_label}", f"Classe {cls_label}")
        return ConstraintExplanation(
            title_he=f"כיתה {cls_label} לא זמינה",
            title_fr=f"Classe {cls_label} indisponible",
            detail_he=f"הכיתה לא יכולה לקבל שיעורים ב{he}.",
            detail_fr=f"La classe ne peut suivre aucun cours sur {fr}.",
            origin=self.origin_description or "מנהל",
            suggestions=[s for s in [sug] if s],
        )


class BlockSlotGroupConstraint(_BlockSlotBase):
    constraint_type = "block_slot_group"

    def _target_groups(self, ctx):
        return [self.target_id] if self.target_id is not None else []

    def explain(self, ctx):
        g_label = f"#{self.target_id}"
        try:
            g = next((g for g in ctx.groups if g.id == self.target_id), None)
            if g:
                g_label = g.label
        except Exception:
            pass
        he = humanize_positions_he(self.positions)
        fr = humanize_positions_fr(self.positions)
        sug = _disable_self_suggestion(self.db_id, f"קבוצה {g_label}", f"Groupe {g_label}")
        return ConstraintExplanation(
            title_he=f"קבוצה «{g_label}» לא זמינה",
            title_fr=f"Groupe « {g_label} » indisponible",
            detail_he=f"הקבוצה לא יכולה להיות משובצת ב{he}.",
            detail_fr=f"Ce groupe ne peut pas être placé sur {fr}.",
            origin=self.origin_description or "מנהל",
            suggestions=[s for s in [sug] if s],
        )


class BlockSlotTeacherConstraint(_BlockSlotBase):
    constraint_type = "block_slot_teacher"

    def _target_groups(self, ctx):
        return ctx.groups_of_teacher(self.target_id) if self.target_id else []

    def explain(self, ctx):
        teacher = None
        teacher_name = f"#{self.target_id}"
        try:
            teacher = ctx.teacher(self.target_id) if self.target_id else None
            if teacher:
                teacher_name = teacher.full_name
        except KeyError:
            pass

        n_blocked = len(self.positions)
        total_slots = len(ctx.all_active_positions())
        n_free = total_slots - n_blocked

        teacher_hours_needed = 0
        if teacher:
            teacher_hours_needed = sum(
                ctx.group(g_id).hours_per_week for g_id in ctx.groups_of_teacher(teacher.id)
            )

        he_positions = humanize_positions_he(self.positions)
        fr_positions = humanize_positions_fr(self.positions)

        if n_blocked > 8:
            detail_he = (
                f"{teacher_name} זמין רק ב-{n_free} משבצות מתוך {total_slots} בשבוע "
                f"(נחוצות {teacher_hours_needed} שעות)."
            )
            detail_fr = (
                f"{teacher_name} n'est disponible que sur {n_free} créneaux/{total_slots} "
                f"par semaine (besoin : {teacher_hours_needed}h)."
            )
        else:
            detail_he = f"{teacher_name} לא יכול ללמד ב{he_positions}."
            detail_fr = f"{teacher_name} ne peut pas enseigner sur {fr_positions}."

        suggestions: list[Suggestion] = []

        sug_disable = _disable_self_suggestion(
            self.db_id, f"זמינות {teacher_name}", f"Indispo {teacher_name}"
        )
        if sug_disable:
            suggestions.append(sug_disable)

        if teacher and n_free < teacher_hours_needed:
            shortage = teacher_hours_needed - n_free
            teacher_groups = sorted(
                (ctx.group(g_id) for g_id in ctx.groups_of_teacher(teacher.id)),
                key=lambda g: -g.hours_per_week,
            )
            if teacher_groups:
                biggest = teacher_groups[0]
                new_h = max(1, biggest.hours_per_week - shortage)
                suggestions.append(Suggestion(
                    kind="reduce_group_hours",
                    title_he=f"צמצם את «{biggest.label}» ל-{new_h} שעות",
                    title_fr=f"Réduire « {biggest.label} » à {new_h}h/sem",
                    description_he=(
                        f"המורה צריך {teacher_hours_needed}ש בשבוע אך זמין רק ל-{n_free}. "
                        f"חוסר של {shortage} שעות."
                    ),
                    description_fr=(
                        f"Le prof a besoin de {teacher_hours_needed}h mais seulement {n_free} dispo. "
                        f"Manque {shortage}h."
                    ),
                    auto_action={
                        "verb": "patch_group",
                        "target_id": biggest.id,
                        "patch": {"hours_per_week": new_h},
                    },
                ))

        if teacher:
            tg_groups = list(ctx.groups_of_teacher(teacher.id))
            for g_id in tg_groups[:2]:
                g = ctx.group(g_id)
                alternates = [
                    t for t in ctx.teachers
                    if t.id != teacher.id
                    and any(s.id == g.subject_id for s in t.qualified_subjects)
                ]
                if alternates:
                    alt_names = ", ".join(t.full_name for t in alternates[:3])
                    suggestions.append(Suggestion(
                        kind="alternative_teacher",
                        title_he=f"שנה מורה ל-«{g.label}»",
                        title_fr=f"Changer de prof pour « {g.label} »",
                        description_he=f"מורים מוסמכים זמינים : {alt_names}",
                        description_fr=f"Profs qualifiés disponibles : {alt_names}",
                    ))

        return ConstraintExplanation(
            title_he=f"זמינות {teacher_name}",
            title_fr=f"Indisponibilité {teacher_name}",
            detail_he=detail_he,
            detail_fr=detail_fr,
            origin=self.origin_description or "המורה",
            suggestions=suggestions,
        )


class BlockSlotRoomConstraint(_BlockSlotBase):
    constraint_type = "block_slot_room"

    def _target_groups(self, ctx):
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

    def explain(self, ctx):
        room = ctx.room(self.target_id) if self.target_id else None
        room_name = room.name if room else f"#{self.target_id}"
        he = humanize_positions_he(self.positions)
        fr = humanize_positions_fr(self.positions)
        sug = _disable_self_suggestion(self.db_id, f"חדר {room_name}", f"Salle {room_name}")
        return ConstraintExplanation(
            title_he=f"חדר לא זמין : {room_name}",
            title_fr=f"Salle indisponible : {room_name}",
            detail_he=f"החדר {room_name} לא ניתן לשימוש ב{he}.",
            detail_fr=f"La salle {room_name} n'est pas utilisable sur {fr}.",
            origin=self.origin_description or "מנהל",
            suggestions=[s for s in [sug] if s],
        )
