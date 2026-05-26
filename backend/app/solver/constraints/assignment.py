"""Contraintes d'AFFECTATION prof / matière / langue (HARD relaxables).

Note importante : dans le modèle v2, l'affectation prof→Group est FIXE
(stockée dans `group_teachers`). Le solveur ne décide pas qui enseigne quoi,
il place le Group dans la grille avec ses profs déjà attribués.

Ces contraintes existent donc surtout pour la VALIDATION (préflight check) :
"Le Group X a le prof Y, mais Y n'est pas qualifié pour la matière de X."
Si une qualification manque, c'est un conflit à signaler à l'utilisateur
AVANT de lancer le solve, ou pendant via une infaisabilité avec MUS.

MVP : on les modélise comme contraintes "tautologiques" — si une affectation
viole la règle, on rend le Group impossible à placer (somme assigned == 0)
sous une assomption, pour que le MUS l'identifie.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.solver.constraints.base import BaseConstraint, ConstraintExplanation

if TYPE_CHECKING:
    from app.solver.context import SolverContext


class TeacherQualifiedForSubjectConstraint(BaseConstraint):
    """Vérifie que tous les profs d'un Group sont qualifiés pour sa matière.

    Params : (aucun — s'applique à tous les groupes, vérifie group.teachers vs group.subject)
    NOTE: cette contrainte est de type "système" — on l'ajoute automatiquement,
    pas via une ligne `constraints` DB.
    """
    constraint_type = "teacher_qualified_for_subject"

    def apply(self, ctx: "SolverContext") -> None:
        violations = []
        for g in ctx.groups:
            qualified_subject_ids = {s.id for t in g.teachers for s in t.qualified_subjects}
            # Si aucun prof n'est qualifié pour cette matière, on a un problème.
            # Vide => on saute (le school admin n'a pas configuré les qualifs)
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

    def explain(self, ctx, lang="fr"):
        return ConstraintExplanation(
            title="Qualification prof / matière",
            detail="Au moins un Group a un prof non qualifié pour sa matière.",
            origin="Vérification système",
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)


class TeacherLanguageRequiredConstraint(BaseConstraint):
    """Le prof d'un Group doit parler la langue requise par la matière.

    Params: language: "fr" | "he"  (la langue dans laquelle la matière doit être enseignée)
            subject_id: int        (à quelle matière s'applique cette règle)
    """
    constraint_type = "teacher_language_required"

    def __init__(self, *, language: str, subject_id: int, **kwargs):
        super().__init__(**kwargs)
        self.language = language
        self.subject_id = subject_id

    def apply(self, ctx: "SolverContext") -> None:
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

    def explain(self, ctx, lang="fr"):
        return ConstraintExplanation(
            title=f"Langue d'enseignement : matière #{self.subject_id}",
            detail=f"Doit être enseignée en {self.language}, certains profs ne la parlent pas.",
            origin=self.origin_description or "Admin école",
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            language=params["language"],
            subject_id=params["subject_id"],
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )
