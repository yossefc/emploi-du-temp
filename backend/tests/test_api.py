"""Tests d'intégration de l'API REST v2 (FastAPI TestClient).

Couvre les endpoints de Phase 4 :
- POST /api/v1/schedules/generate (succès, conflit, timeout)
- GET / DELETE / accept de schedules
- CRUD /api/v1/constraints
- GET /api/v1/constraints/types/schema (introspection pour UI)
"""

from __future__ import annotations

import os

# Doit être set AVANT d'importer app.main (settings init au import)
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-yes-yes")

from datetime import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base, get_db
from app.main import app
from app.models import (
    Class,
    Grade,
    Group,
    GroupingPolicy,
    GroupType,
    Room,
    School,
    Subject,
    Teacher,
    TimeSlot,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def test_db(test_engine):
    Session = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def client(test_engine, test_db):
    """Client FastAPI avec override de la DB pour partager le moteur de test."""
    Session = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    def override_get_db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def setup_school(db, *, days=5, slots=4) -> dict:
    school = School(code="t", name="T")
    db.add(school)
    db.flush()

    for d in range(days):
        for s in range(slots):
            db.add(TimeSlot(
                school_id=school.id, day_of_week=d, slot_index=s,
                start_time=time(8 + s, 0), end_time=time(8 + s, 45),
                is_active=True, is_break=False,
            ))

    grade = Grade(school_id=school.id, code="7", name="7", order=7,
                  grouping_policy=GroupingPolicy.CLASS_CENTRIC)
    db.add(grade)
    db.flush()

    cls = Class(school_id=school.id, grade_id=grade.id, code="7-1", name="7-1",
                student_count=20)
    db.add(cls)

    subj = Subject(school_id=school.id, code="MATH", name_fr="Math", name_he="מתמטיקה")
    db.add(subj)

    t = Teacher(school_id=school.id, code="T1", first_name="A", last_name="B",
                languages=["fr"])
    db.add(t)

    r = Room(school_id=school.id, code="R1", name="Salle 1", capacity=30)
    db.add(r)

    db.commit()
    for o in [school, grade, cls, subj, t, r]:
        db.refresh(o)

    g = Group(school_id=school.id, grade_id=grade.id, subject_id=subj.id,
              label="Math 7-1", hours_per_week=2, group_type=GroupType.WHOLE_CLASS)
    g.teachers.append(t)
    g.source_classes.append(cls)
    db.add(g)
    db.commit()
    db.refresh(g)

    return {"school": school, "grade": grade, "class": cls, "subject": subj,
            "teacher": t, "room": r, "group": g}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_openapi(self, client):
        r = client.get("/api/v1/openapi.json")
        assert r.status_code == 200
        paths = r.json()["paths"]
        assert "/api/v1/schedules/generate" in paths
        assert "/api/v1/constraints" in paths
        assert "/api/v1/constraints/types/schema" in paths


# ---------------------------------------------------------------------------
# Introspection : schemas des params (pour l'UI)
# ---------------------------------------------------------------------------

class TestConstraintsSchema:
    def test_types_schema_returns_all_mvp(self, client):
        r = client.get("/api/v1/constraints/types/schema")
        assert r.status_code == 200
        data = r.json()
        assert "block_slot_teacher" in data
        assert "group_hours_per_week" in data
        assert "extra_hours_at_day_edge" in data
        assert "parameters_schema" in data["block_slot_teacher"]
        assert "class_name" in data["block_slot_teacher"]


# ---------------------------------------------------------------------------
# CRUD contraintes
# ---------------------------------------------------------------------------

class TestConstraintsCRUD:
    def test_create_and_list(self, client, test_db):
        env = setup_school(test_db)
        payload = {
            "school_id": env["school"].id,
            "constraint_type": "block_slot_teacher",
            "priority": "hard",
            "parameters": {
                "days": [0],
                "slot_indices": [0],
                "target_id": env["teacher"].id,
            },
            "origin_role": "teacher",
            "origin_description": "Indispo lundi matin",
        }
        r = client.post("/api/v1/constraints", json=payload)
        assert r.status_code == 201, r.text
        created = r.json()
        assert created["id"]
        assert created["is_active"] is True

        r = client.get(f"/api/v1/constraints?school_id={env['school'].id}")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_patch_deactivate(self, client, test_db):
        env = setup_school(test_db)
        r = client.post("/api/v1/constraints", json={
            "school_id": env["school"].id,
            "constraint_type": "block_slot_teacher",
            "priority": "hard",
            "parameters": {"days": [0], "slot_indices": [0], "target_id": env["teacher"].id},
            "origin_role": "teacher",
        })
        cid = r.json()["id"]
        r2 = client.patch(f"/api/v1/constraints/{cid}", json={"is_active": False})
        assert r2.status_code == 200
        assert r2.json()["is_active"] is False

    def test_delete(self, client, test_db):
        env = setup_school(test_db)
        r = client.post("/api/v1/constraints", json={
            "school_id": env["school"].id,
            "constraint_type": "block_slot_teacher",
            "priority": "hard",
            "parameters": {"days": [0], "slot_indices": [0], "target_id": env["teacher"].id},
            "origin_role": "teacher",
        })
        cid = r.json()["id"]
        r2 = client.delete(f"/api/v1/constraints/{cid}")
        assert r2.status_code == 204
        assert client.get(f"/api/v1/constraints/{cid}").status_code == 404


# ---------------------------------------------------------------------------
# Génération + dialogue conflit (le test phare)
# ---------------------------------------------------------------------------

class TestGenerate:
    def test_generate_success(self, client, test_db):
        env = setup_school(test_db)
        r = client.post("/api/v1/schedules/generate", json={
            "school_id": env["school"].id,
            "name": "API test",
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        assert body["placed_entries"] == 2
        assert body["schedule_id"]

    def test_generate_conflict_then_relax_then_success(self, client, test_db):
        """Cycle complet du dialogue de conflit via l'API REST."""
        env = setup_school(test_db, days=4, slots=1)
        # Pousser à 4h pour saturer les slots dispo
        g = test_db.query(Group).filter_by(id=env["group"].id).one()
        g.hours_per_week = 4
        test_db.commit()

        # Bloquer 3 slots sur 4 → infaisable
        rc = client.post("/api/v1/constraints", json={
            "school_id": env["school"].id,
            "constraint_type": "block_slot_teacher",
            "priority": "hard",
            "parameters": {
                "days": [0, 1, 2], "slot_indices": [0],
                "target_id": env["teacher"].id,
            },
            "origin_role": "teacher",
            "origin_description": "Prof indispo 3 jours",
        })
        assert rc.status_code == 201
        block_id = rc.json()["id"]

        # Etape 1 : conflit
        r1 = client.post("/api/v1/schedules/generate", json={
            "school_id": env["school"].id,
            "max_time_seconds": 5,
        })
        assert r1.status_code == 200
        b1 = r1.json()
        assert b1["success"] is False, f"Expected conflict, got {b1}"
        conflict_ids = [c["constraint_id"] for c in b1["conflicts"]]
        assert block_id in conflict_ids

        # Etape 2 : relax → success
        r2 = client.post("/api/v1/schedules/generate", json={
            "school_id": env["school"].id,
            "name": "After relax",
            "disabled_constraint_ids": [block_id],
            "max_time_seconds": 5,
        })
        assert r2.status_code == 200, r2.text
        b2 = r2.json()
        assert b2["success"] is True
        assert b2["placed_entries"] == 4
        assert block_id in b2["relaxed_constraint_ids"]


# ---------------------------------------------------------------------------
# Lecture + accept schedules
# ---------------------------------------------------------------------------

class TestSchedulesRead:
    def test_get_schedule_with_entries(self, client, test_db):
        env = setup_school(test_db)
        r = client.post("/api/v1/schedules/generate", json={"school_id": env["school"].id})
        sched_id = r.json()["schedule_id"]

        r2 = client.get(f"/api/v1/schedules/{sched_id}")
        assert r2.status_code == 200
        data = r2.json()
        assert data["id"] == sched_id
        assert data["status"] == "draft"
        assert len(data["entries"]) == 2

    def test_accept_promotes_draft(self, client, test_db):
        env = setup_school(test_db)
        sched_id = client.post("/api/v1/schedules/generate",
                                json={"school_id": env["school"].id}).json()["schedule_id"]
        r = client.post(f"/api/v1/schedules/{sched_id}/accept")
        assert r.status_code == 200
        assert r.json()["status"] == "active"

    def test_accept_archives_previous(self, client, test_db):
        env = setup_school(test_db)
        s1 = client.post("/api/v1/schedules/generate",
                          json={"school_id": env["school"].id}).json()["schedule_id"]
        client.post(f"/api/v1/schedules/{s1}/accept")

        s2 = client.post("/api/v1/schedules/generate",
                          json={"school_id": env["school"].id, "name": "v2"}).json()["schedule_id"]
        client.post(f"/api/v1/schedules/{s2}/accept")

        r = client.get(f"/api/v1/schedules/{s1}")
        assert r.json()["status"] == "archived"

    def test_cannot_delete_active(self, client, test_db):
        env = setup_school(test_db)
        sched_id = client.post("/api/v1/schedules/generate",
                                json={"school_id": env["school"].id}).json()["schedule_id"]
        client.post(f"/api/v1/schedules/{sched_id}/accept")
        r = client.delete(f"/api/v1/schedules/{sched_id}")
        assert r.status_code == 400
