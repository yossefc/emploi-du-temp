"""Fixtures pytest pour la suite de tests v2.

Architecture :
- `db_session` : SQLite en mémoire, fresh par test (autocommit off)
- `school`, `another_school` : pour tester l'isolation multi-tenant
- `sample_school_data` : un school COMPLET (grades, classes, profs, subjects, rooms)
  suffisant pour faire tourner le solveur sur des cas simples
"""

from __future__ import annotations

import os
import sys
from datetime import time
from pathlib import Path

# Le backend est le rootdir des tests — pas besoin de chemin spécial
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-used-in-prod")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401 — registre Base.metadata
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


@pytest.fixture
def engine():
    """Engine SQLite in-memory, partagé par toutes les sessions du test."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db_session(engine):
    """Session SQLAlchemy fraîche par test."""
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    s = Session()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


@pytest.fixture
def school(db_session) -> School:
    """Une école vide."""
    s = School(code="amit-netanya", name="AMIT Bar Ilan Netanya")
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


@pytest.fixture
def another_school(db_session) -> School:
    """Deuxième école pour tester l'isolation multi-tenant."""
    s = School(code="other-school", name="Autre école")
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


@pytest.fixture
def time_grid(db_session, school) -> list[TimeSlot]:
    """Grille horaire minimale : 5 jours (dim-jeu) × 4 créneaux."""
    slots = []
    for day in range(5):
        for slot_idx in range(4):
            ts = TimeSlot(
                school_id=school.id,
                day_of_week=day,
                slot_index=slot_idx,
                start_time=time(8 + slot_idx, 0),
                end_time=time(8 + slot_idx, 45),
                is_active=True,
                is_break=False,
            )
            db_session.add(ts)
            slots.append(ts)
    db_session.commit()
    return slots


@pytest.fixture
def sample_school_data(db_session, school, time_grid):
    """Mini-école complète : 1 grade, 2 classes, 3 profs, 2 subjects, 2 rooms.

    Suffisant pour faire tourner le solveur sur un cas non-trivial.

    Renvoie un dict {grade, classes, subjects, teachers, rooms}.
    """
    grade = Grade(school_id=school.id, code="7", name="7e année",
                  order=7, grouping_policy=GroupingPolicy.CLASS_CENTRIC)
    db_session.add(grade)
    db_session.commit()
    db_session.refresh(grade)

    classes = [
        Class(school_id=school.id, grade_id=grade.id, code="7-1", name="7-1", student_count=25),
        Class(school_id=school.id, grade_id=grade.id, code="7-2", name="7-2", student_count=25),
    ]
    db_session.add_all(classes)

    subjects = [
        Subject(school_id=school.id, code="MATH", name_fr="Mathématiques", name_he="מתמטיקה"),
        Subject(school_id=school.id, code="HEB", name_fr="Hébreu", name_he="עברית"),
    ]
    db_session.add_all(subjects)

    teachers = [
        Teacher(school_id=school.id, code="T1", first_name="Sarah", last_name="Cohen",
                languages=["fr", "he"]),
        Teacher(school_id=school.id, code="T2", first_name="David", last_name="Levi",
                languages=["he"]),
        Teacher(school_id=school.id, code="T3", first_name="Rachel", last_name="Mizrahi",
                languages=["fr", "he"]),
    ]
    db_session.add_all(teachers)

    rooms = [
        Room(school_id=school.id, code="R1", name="Salle 101", capacity=30),
        Room(school_id=school.id, code="R2", name="Salle 102", capacity=30),
    ]
    db_session.add_all(rooms)

    db_session.commit()
    for obj in classes + subjects + teachers + rooms:
        db_session.refresh(obj)

    return {
        "grade": grade,
        "classes": classes,
        "subjects": subjects,
        "teachers": teachers,
        "rooms": rooms,
    }
