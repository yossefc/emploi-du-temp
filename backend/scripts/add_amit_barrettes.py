"""Ajoute les ParallelCohorts détectées par extract_amit_v2 à la DB déjà seedée.

À lancer APRÈS seed_amit.py.

Stratégie :
- Lit amit_data_v2.json (grade_barrettes)
- Filtre : ne garde que les barrettes "académiquement valides" :
  * Religieux : TANACH+TANACH_M, TALMUD+TALMUD_M, TORAH_BAAL+TALMUD_M
  * Hebrew triple : HEVANA+HABAA_M+HEBREW
  * Tech tracks (G10+) : CS+ELEC+PHYSICS, CS+FRENCH+PHYSICS, etc.
- Pour chaque barrette validée : crée une ParallelCohort par שכבה,
  et lie les Groups correspondants (matière dans le set + grade match)
- Ajuste hours_per_week : pour les groups en barrette, on prend la moyenne pondérée
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")

from sqlalchemy.orm import sessionmaker

from app.db.base import engine
import app.models  # noqa: F401
from app.models import Grade, Group, ParallelCohort, School, Subject


DATA_PATH = Path(__file__).parent / "amit_data_v2.json"


# Barrettes validées manuellement (filtre du bruit G9)
VALIDATED_BARRETTES = {
    # Religieux : barrettes שכבה-wide pour toutes les שכבות
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
}


def main():
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = Session()

    school = db.query(School).filter_by(code="amit-netanya").first()
    if not school:
        print("École amit-netanya non trouvée — lance seed_amit.py d'abord.")
        return

    # Index grade code → Grade obj
    grades_by_code = {g.code: g for g in db.query(Grade).filter_by(school_id=school.id).all()}
    # Index subject code → Subject obj
    subjects_by_code = {s.code: s for s in db.query(Subject).filter_by(school_id=school.id).all()}

    n_cohorts = 0
    n_groups_linked = 0

    for barrette_subjects, target_grades in VALIDATED_BARRETTES.items():
        # Vérifier que les matières existent
        if not all(s in subjects_by_code for s in barrette_subjects):
            missing = [s for s in barrette_subjects if s not in subjects_by_code]
            print(f"  ⚠ Barrette {barrette_subjects} : matières manquantes {missing}")
            continue

        subject_ids = [subjects_by_code[s].id for s in barrette_subjects]

        for grade_code in target_grades:
            if grade_code not in grades_by_code:
                continue
            grade = grades_by_code[grade_code]

            # Vérifier qu'on a au moins 1 group pour chaque matière dans cette שכבה
            groups_per_subject = {}
            for s_code in barrette_subjects:
                s_id = subjects_by_code[s_code].id
                gs = (
                    db.query(Group)
                    .filter(
                        Group.school_id == school.id,
                        Group.grade_id == grade.id,
                        Group.subject_id == s_id,
                    )
                    .all()
                )
                if not gs:
                    continue
                groups_per_subject[s_code] = gs

            if len(groups_per_subject) < 2:
                # Pas assez de matières trouvées dans cette שכבה
                continue

            # Créer la ParallelCohort
            label = " + ".join(sorted(barrette_subjects))
            cohort = ParallelCohort(
                school_id=school.id, grade_id=grade.id,
                label=f"הקבצה {label} ({grade.code})",
            )
            db.add(cohort)
            db.flush()
            n_cohorts += 1

            # Lier les groups : pour chaque (matière, group) on assigne le cohort
            # On prend SEULEMENT le 1er group par matière par classe (sinon explosion)
            # Et on force hours_per_week à 3 (commun pour barrette religieuse/Hebrew)
            for s_code, gs in groups_per_subject.items():
                # Heuristique : si SHEKHVA-wide (TANACH+TANACH_M), un seul "rep group" par matière
                # qui couvre toutes les classes du grade. Trop complexe pour l'instant.
                # On lie tous les groups individuels au cohort.
                for g in gs:
                    g.parallel_cohort_id = cohort.id
                    # Réduire les hours si trop élevées (les barrettes sont en général 3-5h)
                    if g.hours_per_week > 5:
                        g.hours_per_week = 5
                    n_groups_linked += 1

    db.commit()

    print(f"\n✅ {n_cohorts} ParallelCohorts créées")
    print(f"   {n_groups_linked} groups liés à une cohort")

    # Statistiques finales
    total_groups = db.query(Group).filter_by(school_id=school.id).count()
    groups_in_cohort = db.query(Group).filter(
        Group.school_id == school.id,
        Group.parallel_cohort_id.isnot(None),
    ).count()
    print(f"\n   Stats : {groups_in_cohort}/{total_groups} groups en barrette")


if __name__ == "__main__":
    main()
