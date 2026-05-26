"""Tests d'intégration du flow wizard : créer une école complète step-by-step
via l'API REST, puis lancer une génération."""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-yes-yes")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base, get_db
from app.main import app


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
def client(test_engine):
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


class TestWizardFlow:
    def test_full_wizard_creates_working_school(self, client):
        """Simule le flow du wizard admin : on monte une école complète via
        l'API REST, puis on lance une génération qui doit réussir."""

        # ---- Step 1 : créer l'école ----
        r = client.post("/api/v1/schools", json={
            "code": "test-school",
            "name": "École Test",
            "default_language": "fr",
        })
        assert r.status_code == 201, r.text
        school_id = r.json()["id"]

        # ---- Step 2 : poser la grille horaire (bulk) ----
        slots = []
        for day in range(3):
            for slot in range(3):
                slots.append({
                    "day_of_week": day, "slot_index": slot,
                    "start_time": f"{8+slot:02d}:00:00",
                    "end_time": f"{8+slot:02d}:45:00",
                    "is_active": True, "is_break": False,
                })
        r = client.post(f"/api/v1/schools/{school_id}/time-grid", json={"slots": slots})
        assert r.status_code == 200, r.text
        assert len(r.json()) == 9

        # ---- Step 3 : créer un Grade ----
        r = client.post("/api/v1/grades", json={
            "school_id": school_id,
            "code": "10", "name": "10e année", "order": 10,
            "grouping_policy": "class_centric",
        })
        assert r.status_code == 201, r.text
        grade_id = r.json()["id"]

        # ---- Step 4 : créer une Class ----
        r = client.post("/api/v1/classes", json={
            "school_id": school_id, "grade_id": grade_id,
            "code": "10-1", "name": "10A", "student_count": 25,
        })
        assert r.status_code == 201, r.text
        class_id = r.json()["id"]

        # ---- Step 5 : créer une Subject ----
        r = client.post("/api/v1/subjects", json={
            "school_id": school_id,
            "code": "PHYS", "name_fr": "Physique", "name_he": "פיזיקה",
        })
        assert r.status_code == 201, r.text
        subject_id = r.json()["id"]

        # ---- Step 6 : créer un Teacher avec qualification ----
        r = client.post("/api/v1/teachers", json={
            "school_id": school_id,
            "code": "T1", "first_name": "Albert", "last_name": "Einstein",
            "languages": ["fr"],
            "qualified_subject_ids": [subject_id],
        })
        assert r.status_code == 201, r.text
        teacher_id = r.json()["id"]
        assert r.json()["qualified_subject_ids"] == [subject_id]

        # ---- Step 7 : créer une Room ----
        r = client.post("/api/v1/rooms", json={
            "school_id": school_id, "code": "L1", "name": "Labo physique",
            "capacity": 30, "room_type": "lab",
        })
        assert r.status_code == 201, r.text
        room_id = r.json()["id"]

        # ---- Step 8 : créer un Group qui assemble tout ----
        r = client.post("/api/v1/groups", json={
            "school_id": school_id, "grade_id": grade_id, "subject_id": subject_id,
            "label": "Physique 10-1", "hours_per_week": 2,
            "group_type": "whole_class",
            "teacher_ids": [teacher_id],
            "source_class_ids": [class_id],
        })
        assert r.status_code == 201, r.text
        group_id = r.json()["id"]
        assert r.json()["teacher_ids"] == [teacher_id]
        assert r.json()["source_class_ids"] == [class_id]

        # ---- Step 9 : lister chaque entité pour vérifier ----
        for path, expected in [
            ("/api/v1/schools", 1),
            (f"/api/v1/grades?school_id={school_id}", 1),
            (f"/api/v1/classes?school_id={school_id}", 1),
            (f"/api/v1/subjects?school_id={school_id}", 1),
            (f"/api/v1/teachers?school_id={school_id}", 1),
            (f"/api/v1/rooms?school_id={school_id}", 1),
            (f"/api/v1/groups?school_id={school_id}", 1),
        ]:
            r = client.get(path)
            assert r.status_code == 200, f"{path}: {r.text}"
            assert len(r.json()) == expected, f"{path}: expected {expected}, got {len(r.json())}"

        # ---- Step 10 : lancer la génération ----
        r = client.post("/api/v1/schedules/generate", json={
            "school_id": school_id, "name": "Wizard test",
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True, f"Generation failed: {body}"
        assert body["placed_entries"] == 2  # 2 hours of Physics

    def test_school_list_returns_all_schools(self, client):
        """Schools n'a pas de school_id filter — liste toutes les écoles."""
        for code in ["a", "b", "c"]:
            client.post("/api/v1/schools", json={"code": code, "name": code.upper()})
        r = client.get("/api/v1/schools")
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_grades_require_school_id(self, client):
        """Liste sans school_id → 400 pour les entités scoped."""
        r = client.get("/api/v1/grades")
        assert r.status_code == 400

    def test_time_grid_replace_is_atomic(self, client):
        r = client.post("/api/v1/schools", json={"code": "x", "name": "X"})
        school_id = r.json()["id"]

        # Première grille
        slots_v1 = [{
            "day_of_week": 0, "slot_index": 0,
            "start_time": "08:00:00", "end_time": "08:45:00",
        }]
        r = client.post(f"/api/v1/schools/{school_id}/time-grid", json={"slots": slots_v1})
        assert r.status_code == 200
        assert len(r.json()) == 1

        # Remplacer par une grille v2 (les v1 doivent disparaître)
        slots_v2 = [
            {"day_of_week": 0, "slot_index": 0, "start_time": "09:00:00", "end_time": "09:45:00"},
            {"day_of_week": 1, "slot_index": 0, "start_time": "09:00:00", "end_time": "09:45:00"},
        ]
        r = client.post(f"/api/v1/schools/{school_id}/time-grid", json={"slots": slots_v2})
        assert r.status_code == 200
        assert len(r.json()) == 2

        # Vérifier que c'est bien la v2 (heure de début 9h, pas 8h)
        r = client.get(f"/api/v1/schools/{school_id}/time-grid")
        assert len(r.json()) == 2
        assert all(s["start_time"].startswith("09") for s in r.json())

    def test_cohort_with_groups_returns_group_ids(self, client):
        """Vérif que ParallelCohortRead retourne bien les group_ids dérivés."""
        # Setup minimum
        sid = client.post("/api/v1/schools", json={"code": "s", "name": "S"}).json()["id"]
        for d in range(2):
            for s in range(2):
                client.post(f"/api/v1/schools/{sid}/time-grid", json={
                    "slots": [{"day_of_week": d, "slot_index": s,
                                "start_time": f"{8+s:02d}:00:00", "end_time": f"{8+s:02d}:45:00"}]
                }) if d == 0 and s == 0 else None
        # On utilise plutôt un POST batch
        client.post(f"/api/v1/schools/{sid}/time-grid", json={"slots": [
            {"day_of_week": d, "slot_index": s, "start_time": f"{8+s:02d}:00:00", "end_time": f"{8+s:02d}:45:00"}
            for d in range(3) for s in range(3)
        ]})
        gid = client.post("/api/v1/grades", json={"school_id": sid, "code": "9", "name": "9", "order": 9}).json()["id"]
        cid = client.post("/api/v1/classes", json={"school_id": sid, "grade_id": gid, "code": "9-1", "name": "9A"}).json()["id"]
        subj = client.post("/api/v1/subjects", json={"school_id": sid, "code": "M", "name_fr": "M", "name_he": "מ"}).json()["id"]
        t = client.post("/api/v1/teachers", json={"school_id": sid, "code": "T", "first_name": "T", "last_name": "T"}).json()["id"]

        # Cohorte
        cohort = client.post("/api/v1/cohorts", json={"school_id": sid, "grade_id": gid, "label": "Barrette"}).json()
        assert cohort["group_ids"] == []

        # Ajouter 2 groups dans la cohorte
        for i in range(2):
            client.post("/api/v1/groups", json={
                "school_id": sid, "grade_id": gid, "subject_id": subj,
                "label": f"G{i}", "hours_per_week": 1, "group_type": "level_group",
                "parallel_cohort_id": cohort["id"],
                "teacher_ids": [t], "source_class_ids": [cid],
            })

        r = client.get(f"/api/v1/cohorts/{cohort['id']}")
        assert len(r.json()["group_ids"]) == 2
