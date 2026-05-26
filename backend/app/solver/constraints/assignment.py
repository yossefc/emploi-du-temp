"""Contraintes d'AFFECTATION prof / matière / langue — bilingues."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.solver.constraints.base import BaseConstraint, ConstraintExplanation

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
        return ConstraintExplanation(
            title_he="הסמכת מורה / מקצוע",
            title_fr="Qualification prof / matière",
            detail_he="לפחות קבוצה אחת מוקצית למורה שאינו מוסמך למקצוע שלה.",
            detail_fr="Au moins un Group a un prof non qualifié pour sa matière.",
            origin="בדיקת מערכת",
            suggestions=[],
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
        return ConstraintExplanation(
            title_he=f"שפת לימוד : מקצוע #{self.subject_id}",
            title_fr=f"Langue d'enseignement : matière #{self.subject_id}",
            detail_he=f"המקצוע חייב להילמד ב{self.language}, אך מורים מסוימים לא דוברים אותה.",
            detail_fr=f"Doit être enseignée en {self.language}, certains profs ne la parlent pas.",
            origin=self.origin_description or "מנהל",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(language=params["language"], subject_id=params["subject_id"],
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)
