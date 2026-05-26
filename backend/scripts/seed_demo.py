"""Seed une mini-école inspirée d'AMIT Bar Ilan Netanya pour tester l'API.

Usage :
    DATABASE_URL='sqlite:///./demo.db' SECRET_KEY='...' python scripts/seed_demo.py

Crée :
- 1 école "AMIT Démo"
- Grille : Dim-Jeu, 8 créneaux/jour de 8h à 15h45
- 1 שכבה ז (7e année) avec 2 classes (7-1, 7-2)
- 2 matières : Math, Hébreu
- 3 profs avec qualifications
- 2 salles
- 4 Groups :
  * Hébreu pour 7-1 et 7-2 (cours classe)
  * Math en barrette inter-classes (2 niveaux: fort/normal) dans une ParallelCohort
"""

from __future__ import annotations

import os
import sys
from datetime import time
from pathlib import Path

# Permettre l'import depuis backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")

from sqlalchemy.orm import sessionmaker

from app.db.base import engine
import app.models  # noqa: F401
from app.models import (
    Class,
    Grade,
    Group,
    GroupType,
    GroupingPolicy,
    ParallelCohort,
    Room,
    School,
    Subject,
    Teacher,
    TimeSlot,
)


def main():
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = Session()

    # Si l'école démo existe déjà, on s'arrête (idempotent)
    if db.query(School).filter_by(code="amit-demo").first():
        print("École 'amit-demo' déjà seedée. Supprime demo.db pour repartir à zéro.")
        return

    school = School(code="amit-demo", name="AMIT Démo", default_language="fr")
    db.add(school)
    db.flush()
    print(f"+ School #{school.id}: {school.name}")

    # Grille horaire : Dim (0) à Jeu (4), 8 créneaux 8h-15h45
    for day in range(5):
        for slot in range(8):
            start_h = 8 + slot
            db.add(TimeSlot(
                school_id=school.id,
                day_of_week=day, slot_index=slot,
                start_time=time(start_h, 0),
                end_time=time(start_h, 45),
                is_active=True, is_break=False,
                label=f"Créneau {slot+1}",
            ))
    db.flush()
    print(f"+ 40 TimeSlots (5 jours × 8 créneaux)")

    grade7 = Grade(
        school_id=school.id, code="ז", name="7e année", order=7,
        grouping_policy=GroupingPolicy.GROUP_CENTRIC,
    )
    db.add(grade7)
    db.flush()
    print(f"+ Grade #{grade7.id}: שכבה ז (7e)")

    cls71 = Class(school_id=school.id, grade_id=grade7.id, code="7-1", name="Septième 1", student_count=24)
    cls72 = Class(school_id=school.id, grade_id=grade7.id, code="7-2", name="Septième 2", student_count=22)
    db.add_all([cls71, cls72])
    db.flush()
    print(f"+ Classes: 7-1 (#{cls71.id}, {cls71.student_count} él.), 7-2 (#{cls72.id}, {cls72.student_count} él.)")

    subj_math = Subject(school_id=school.id, code="MATH", name_fr="Mathématiques", name_he="מתמטיקה",
                         color_hex="#3B82F6", abbreviation="MATH")
    subj_heb = Subject(school_id=school.id, code="HEB", name_fr="Hébreu", name_he="עברית",
                        color_hex="#10B981", abbreviation="HEB")
    db.add_all([subj_math, subj_heb])
    db.flush()
    print(f"+ Subjects: Math (#{subj_math.id}), Hébreu (#{subj_heb.id})")

    t_levi = Teacher(school_id=school.id, code="LEVI", first_name="David", last_name="Lévi",
                      email="levi@amit.test", languages=["he", "fr"], max_hours_per_week=24)
    t_cohen = Teacher(school_id=school.id, code="COHEN", first_name="Sarah", last_name="Cohen",
                       email="cohen@amit.test", languages=["he", "fr"], max_hours_per_week=24)
    t_mizrahi = Teacher(school_id=school.id, code="MIZ", first_name="Rachel", last_name="Mizrahi",
                         email="mizrahi@amit.test", languages=["he"], max_hours_per_week=24)
    db.add_all([t_levi, t_cohen, t_mizrahi])
    db.flush()
    # Qualifications : Levi+Cohen math ; Mizrahi hébreu
    t_levi.qualified_subjects.append(subj_math)
    t_cohen.qualified_subjects.append(subj_math)
    t_mizrahi.qualified_subjects.append(subj_heb)
    db.flush()
    print(f"+ Profs: Lévi (Math), Cohen (Math), Mizrahi (Hébreu)")

    r1 = Room(school_id=school.id, code="101", name="Salle 101", capacity=30)
    r2 = Room(school_id=school.id, code="102", name="Salle 102", capacity=30)
    db.add_all([r1, r2])
    db.flush()
    print(f"+ Rooms: 101, 102")

    # ==================== Groups ====================
    # Hébreu : 1 group par classe (cours classe entière)
    g_heb_71 = Group(school_id=school.id, grade_id=grade7.id, subject_id=subj_heb.id,
                      label="Hébreu 7-1", hours_per_week=3,
                      group_type=GroupType.WHOLE_CLASS, student_count=24)
    g_heb_71.teachers.append(t_mizrahi)
    g_heb_71.source_classes.append(cls71)

    g_heb_72 = Group(school_id=school.id, grade_id=grade7.id, subject_id=subj_heb.id,
                      label="Hébreu 7-2", hours_per_week=3,
                      group_type=GroupType.WHOLE_CLASS, student_count=22)
    g_heb_72.teachers.append(t_mizrahi)
    g_heb_72.source_classes.append(cls72)

    db.add_all([g_heb_71, g_heb_72])
    db.flush()

    # Math : barrette inter-classes (שכבה-wide)
    cohort_math = ParallelCohort(school_id=school.id, grade_id=grade7.id,
                                  label="Math barrette שכבה ז")
    db.add(cohort_math)
    db.flush()

    # 2 niveaux : fort (Levi) et normal (Cohen). 4h chacun pour cet exemple.
    g_math_fort = Group(school_id=school.id, grade_id=grade7.id, subject_id=subj_math.id,
                         label="Math fort", hours_per_week=4,
                         group_type=GroupType.LEVEL_GROUP, parallel_cohort_id=cohort_math.id,
                         student_count=20)
    g_math_fort.teachers.append(t_levi)
    g_math_fort.source_classes.extend([cls71, cls72])

    g_math_normal = Group(school_id=school.id, grade_id=grade7.id, subject_id=subj_math.id,
                           label="Math normal", hours_per_week=4,
                           group_type=GroupType.LEVEL_GROUP, parallel_cohort_id=cohort_math.id,
                           student_count=26)
    g_math_normal.teachers.append(t_cohen)
    g_math_normal.source_classes.extend([cls71, cls72])

    db.add_all([g_math_fort, g_math_normal])
    db.commit()

    print(f"+ Groups:")
    print(f"  - Hébreu 7-1 (3h, prof Mizrahi)")
    print(f"  - Hébreu 7-2 (3h, prof Mizrahi)")
    print(f"  - Math fort (4h, prof Lévi)    ] cohorte parallèle")
    print(f"  - Math normal (4h, prof Cohen) ] mêmes créneaux")
    print()
    print("Total: 14 cours à placer dans 40 créneaux (Math fort + normal partagent les créneaux)")
    print()
    print("✅ Seed terminé. school_id =", school.id)


if __name__ == "__main__":
    main()
