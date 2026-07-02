"""Construit les barrettes (הקבצות) AMIT — version FUSION שכבה-wide.

À lancer APRÈS seed_amit.py.

Pourquoi la fusion ?
Le seed crée 1 Group par (matière, classe) : HEVANA ז-1, HEVANA ז-2, …
Si on liait ces 4 groups dans une cohorte, la contrainte "même créneau"
forcerait le prof partagé (ex: חדד מוראל enseigne l'hébreu aux 4 classes)
à donner 4 cours SIMULTANÉMENT → TeacherNoOverlap → INFEASIBLE.

La réalité AMIT (visible dans le PDF iscool) : une matière en barrette est
UN cours שכבה-wide — une cellule "הבנה והבעה" avec 3 profs = 3 sous-groupes
de niveau qui tournent en même temps, chacun son prof. Pour le solveur,
c'est UN Group multi-profs couvrant toutes les classes de la שכבה :
tous les profs sont occupés à ce créneau, toutes les classes aussi.

Ce script :
1. Pour chaque barrette validée (set de matières × שכבה) :
   - fusionne les groups par-classe de chaque matière en un group שכבה-wide
     (union des profs, union des classes, hours = max)
   - supprime les groups fusionnés
2. Crée la ParallelCohort et y lie les groups fusionnés (1 par matière/track)

Sémantique solveur (ParallelCohortSameSlot, version enveloppe) :
- les tracks au volume max tournent exactement ensemble
- les tracks plus courts tournent dans l'enveloppe des longs
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")

from sqlalchemy.orm import sessionmaker

from app.db.base import engine
import app.models  # noqa: F401
from app.models import Grade, Group, GroupType, ParallelCohort, School, Subject


# Barrettes validées depuis l'analyse du PDF (extract_amit_v2)
VALIDATED_BARRETTES = {
    # Religieux : barrettes שכבה-wide
    frozenset({"TANACH", "TANACH_M"}): {"G7", "G8", "G9", "G10", "G11"},
    frozenset({"TORAH_BAAL", "TALMUD_M"}): {"G7", "G8", "G9"},
    frozenset({"TALMUD", "TALMUD_M"}): {"G10", "G11", "G12"},

    # Hebrew triple-track (collège)
    frozenset({"HEVANA", "HABAA_M", "HEBREW"}): {"G7", "G8"},
    frozenset({"HEVANA", "HABAA_M"}): {"G9"},

    # Tech tracks (lycée — choix élève)
    frozenset({"CS", "ELEC", "PHYSICS"}): {"G10", "G12"},
    frozenset({"ELEC", "PHYSICS"}): {"G10"},
    frozenset({"CS", "FRENCH", "PHYSICS"}): {"G11"},

    # Math en niveaux : LE cas classique israélien (5/4/3 yehidot).
    # Le PDF montre Math avec 5 profs simultanés sur la שכבה → fusion.
    frozenset({"MATH"}): {"G7", "G8", "G9", "G10", "G11", "G12"},
    # Anglais idem (4 profs simultanés dans le PDF)
    frozenset({"ENGLISH"}): {"G7", "G8", "G9", "G10", "G11", "G12"},
}


def merge_groups_of_subject(db, school_id: int, grade: Grade, subject: Subject) -> Group | None:
    """Fusionne tous les groups (subject, grade) en un seul שכבה-wide.

    Retourne le group fusionné (ou l'unique existant), None si aucun.
    """
    groups = (
        db.query(Group)
        .filter(
            Group.school_id == school_id,
            Group.grade_id == grade.id,
            Group.subject_id == subject.id,
        )
        .all()
    )
    if not groups:
        return None
    if len(groups) == 1:
        return groups[0]

    keeper = groups[0]
    all_teachers = {t.id: t for t in keeper.teachers}
    all_classes = {c.id: c for c in keeper.source_classes}
    max_hours = keeper.hours_per_week
    total_students = keeper.student_count or 0

    for g in groups[1:]:
        for t in g.teachers:
            all_teachers.setdefault(t.id, t)
        for c in g.source_classes:
            all_classes.setdefault(c.id, c)
        max_hours = max(max_hours, g.hours_per_week)
        total_students += g.student_count or 0
        db.delete(g)

    keeper.teachers = list(all_teachers.values())
    keeper.source_classes = list(all_classes.values())
    keeper.hours_per_week = min(max_hours, 5)  # cap raisonnable
    keeper.student_count = total_students
    keeper.group_type = GroupType.LEVEL_GROUP
    keeper.label = f"{subject.name_he} {grade.name}"
    db.flush()
    return keeper


def main():
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = Session()

    school = db.query(School).filter_by(code="amit-netanya").first()
    if not school:
        print("École amit-netanya non trouvée — lance seed_amit.py d'abord.")
        return

    grades_by_code = {g.code: g for g in db.query(Grade).filter_by(school_id=school.id).all()}
    subjects_by_code = {s.code: s for s in db.query(Subject).filter_by(school_id=school.id).all()}

    n_cohorts = 0
    n_merged = 0
    groups_before = db.query(Group).filter_by(school_id=school.id).count()

    for barrette_subjects, target_grades in VALIDATED_BARRETTES.items():
        missing = [s for s in barrette_subjects if s not in subjects_by_code]
        if missing:
            print(f"  ⚠ Barrette {set(barrette_subjects)} : matières manquantes {missing}")
            continue

        for grade_code in target_grades:
            grade = grades_by_code.get(grade_code)
            if grade is None:
                continue

            # Fusionner chaque matière de la barrette en un group שכבה-wide
            merged_groups: list[Group] = []
            for s_code in barrette_subjects:
                subj = subjects_by_code[s_code]
                g = merge_groups_of_subject(db, school.id, grade, subj)
                if g is not None:
                    merged_groups.append(g)

            if len(merged_groups) < 2:
                # Barrette mono-matière (MATH, ENGLISH) : la fusion suffit,
                # pas besoin de cohorte (un seul group שכבה-wide).
                continue

            label = " + ".join(sorted(barrette_subjects))
            cohort = ParallelCohort(
                school_id=school.id, grade_id=grade.id,
                label=f"הקבצה {label} ({grade.code})",
            )
            db.add(cohort)
            db.flush()
            n_cohorts += 1

            for g in merged_groups:
                g.parallel_cohort_id = cohort.id

    db.commit()

    groups_after = db.query(Group).filter_by(school_id=school.id).count()
    n_merged = groups_before - groups_after
    in_cohort = db.query(Group).filter(
        Group.school_id == school.id, Group.parallel_cohort_id.isnot(None)
    ).count()

    print(f"\n✅ Barrettes construites (mode fusion שכבה-wide)")
    print(f"   Groups : {groups_before} → {groups_after} ({n_merged} fusionnés)")
    print(f"   {n_cohorts} ParallelCohorts, {in_cohort} groups en cohorte")


if __name__ == "__main__":
    main()
