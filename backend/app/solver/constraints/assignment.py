"""Contraintes d'AFFECTATION prof / matière / langue — bilingues."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.solver.constraints.base import BaseConstraint, ConstraintExplanation, Suggestion

if TYPE_CHECKING:
    from app.solver.context import SolverContext


class TeacherQualifiedForSubjectConstraint(BaseConstraint):
    constraint_type = "teacher_qualified_for_subject"

    def apply(self, ctx):
        violations = []
        for g in ctx.groups:
            qualified_subject_ids = {s.id for t in g.teachers for s in t.qualified_subjects}
            if not qualified_subject_ids:
                continue
            if g.subject_id not in qualified_subject_ids:
                violations.append(g.id)
        if not violations:
            return
        lit = ctx.model.NewBoolVar(f"assum_qualif_{self.db_id or 'sys'}")
        self.assumption_literal = lit
        for g_id in violations:
            for var in ctx.assigned[g_id].values():
                ctx.model.Add(var == 0).OnlyEnforceIf(lit)

    def explain(self, ctx):
        # Identifier les violations spécifiques pour suggestions
        suggestions = []
        violations = []
        for g in ctx.groups:
            qualified_subject_ids = {s.id for t in g.teachers for s in t.qualified_subjects}
            if qualified_subject_ids and g.subject_id not in qualified_subject_ids:
                violations.append(g)

        for g in violations[:3]:  # max 3 suggestions
            # Chercher des profs qualifiés disponibles
            alternates = [
                t for t in ctx.teachers
                if any(s.id == g.subject_id for s in t.qualified_subjects)
            ]
            if alternates:
                alt = alternates[0]
                suggestions.append(Suggestion(
                    kind="change_group_teacher",
                    title_he=f"החלף את המורה של «{g.label}» ל-{alt.full_name}",
                    title_fr=f"Remplacer le prof de « {g.label} » par {alt.full_name}",
                    description_he=f"{alt.full_name} מוסמך למקצוע זה.",
                    description_fr=f"{alt.full_name} est qualifié pour cette matière.",
                    auto_action={
                        "verb": "patch_group", "target_id": g.id,
                        "patch": {"teacher_ids": [alt.id]},
                    },
                ))
            else:
                # Pas d'alternative — suggérer d'ajouter la qualif au prof actuel
                current = g.teachers[0] if g.teachers else None
                if current:
                    new_qualifs = [s.id for s in current.qualified_subjects] + [g.subject_id]
                    suggestions.append(Suggestion(
                        kind="add_qualification",
                        title_he=f"הוסף הסמכה ל-{current.full_name}",
                        title_fr=f"Ajouter la qualif à {current.full_name}",
                        description_he="הוסף את המקצוע לרשימת ההסמכות של המורה הנוכחי.",
                        description_fr="Ajoute cette matière aux qualifs du prof actuel.",
                        auto_action={
                            "verb": "patch_constraint", "target_id": current.id,  # à corriger : c'est un teacher, pas constraint
                            "patch": {"qualified_subject_ids": new_qualifs},
                        },
                    ))

        return ConstraintExplanation(
            title_he="הסמכת מורה / מקצוע",
            title_fr="Qualification prof / matière",
            detail_he=(
                f"{len(violations)} קבוצות מוקצות למורים שאינם מוסמכים למקצוע."
                if violations else "לפחות קבוצה אחת מוקצית למורה שאינו מוסמך."
            ),
            detail_fr=(
                f"{len(violations)} groupe(s) ont des profs non qualifiés."
                if violations else "Au moins un Group a un prof non qualifié."
            ),
            origin="בדיקת מערכת",
            suggestions=suggestions,
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)


class TeacherLanguageRequiredConstraint(BaseConstraint):
    constraint_type = "teacher_language_required"

    def __init__(self, *, language: str, subject_id: int, **kwargs):
        super().__init__(**kwargs)
        self.language = language
        self.subject_id = subject_id

    def apply(self, ctx):
        violations = []
        for g in ctx.groups:
            if g.subject_id != self.subject_id:
                continue
            for t in g.teachers:
                if self.language not in (t.languages or []):
                    violations.append(g.id)
                    break
        if not violations:
            return
        lit = ctx.model.NewBoolVar(f"assum_lang_{self.db_id or 'sys'}")
        self.assumption_literal = lit
        for g_id in violations:
            for var in ctx.assigned[g_id].values():
                ctx.model.Add(var == 0).OnlyEnforceIf(lit)

    def explain(self, ctx):
        # Identifier les groups en violation et chercher des profs qui parlent la langue
        suggestions = []
        lang_speakers = [t for t in ctx.teachers if self.language in (t.languages or [])]

        violations = []
        for g in ctx.groups:
            if g.subject_id != self.subject_id:
                continue
            non_speakers = [t for t in g.teachers if self.language not in (t.languages or [])]
            if non_speakers:
                violations.append(g)

        for g in violations[:3]:
            qualified_speakers = [
                t for t in lang_speakers
                if any(s.id == self.subject_id for s in t.qualified_subjects)
            ]
            if qualified_speakers:
                alt = qualified_speakers[0]
                suggestions.append(Suggestion(
                    kind="change_group_teacher",
                    title_he=f"החלף את המורה של «{g.label}» ל-{alt.full_name}",
                    title_fr=f"Remplacer le prof de « {g.label} » par {alt.full_name}",
                    description_he=f"{alt.full_name} מוסמך וגם דובר {self.language}.",
                    description_fr=f"{alt.full_name} est qualifié ET parle {self.language}.",
                    auto_action={
                        "verb": "patch_group", "target_id": g.id,
                        "patch": {"teacher_ids": [alt.id]},
                    },
                ))

        if self.db_id:
            suggestions.append(Suggestion(
                kind="disable_constraint",
                title_he=f"בטל את הדרישה לשפת {self.language}",
                title_fr=f"Désactiver l'exigence de langue {self.language}",
                description_he="כל המורים יוכלו ללמד את המקצוע.",
                description_fr="Tous les profs pourront enseigner cette matière.",
                auto_action={"verb": "patch_constraint", "target_id": self.db_id, "patch": {"is_active": False}},
            ))

        return ConstraintExplanation(
            title_he=f"שפת לימוד : מקצוע #{self.subject_id}",
            title_fr=f"Langue d'enseignement : matière #{self.subject_id}",
            detail_he=f"המקצוע חייב להילמד ב{self.language}, אך מורים מסוימים לא דוברים אותה.",
            detail_fr=f"Doit être enseignée en {self.language}, certains profs ne la parlent pas.",
            origin=self.origin_description or "מנהל",
            suggestions=suggestions,
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(language=params["language"], subject_id=params["subject_id"],
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)
