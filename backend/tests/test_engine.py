"""Tests d'intégration de l'engine — bout en bout : DB → solve → ScheduleEntry.

Couvre :
- Succès : génération d'un planning faisable, vérification des ScheduleEntry créés
- Conflit : INFEASIBLE → liste de contraintes en conflit retournée (avec leur DB id)
- Cycle dialogue : conflit → relax → re-solve → success
- Barrette : ParallelCohort respectée dans la solution
- Multi-tenant : engine d'une école ne voit pas l'autre
"""

from __future__ import annotations

from datetime import time

import pytest

from app.models import (
    Class,
    Constraint as DBConstraint,
    ConstraintOriginRole,
    ConstraintPriority,
    ConstraintType,
    Grade,
    Group,
    GroupType,
    GroupingPolicy,
    ParallelCohort,
    Room,
    Schedule,
    ScheduleEntry,
    School,
    Subject,
    Teacher,
    TimeSlot,
)
from app.solver import (
    SolveConflict,
    SolveSuccess,
    SolveTimeout,
    TimetableEngine,
)


# ---------------------------------------------------------------------------
# Helpers : monter un mini-school complet pour le solveur
# ---------------------------------------------------------------------------

def setup_minimal_school(db_session, *, days: int = 5, slots_per_day: int = 4) -> dict:
    """Monte une école minimaliste : 1 grade, 2 classes, 2 profs, 1 matière, 2 salles."""
    school = School(code="testschool", name="Test School")
    db_session.add(school)
    db_session.flush()

    for d in range(days):
        for s in range(slots_per_day):
            db_session.add(TimeSlot(
                school_id=school.id, day_of_week=d, slot_index=s,
                start_time=time(8 + s, 0), end_time=time(8 + s, 45),
                is_active=True, is_break=False,
            ))

    grade = Grade(school_id=school.id, code="7", name="7", order=7,
                  grouping_policy=GroupingPolicy.CLASS_CENTRIC)
    db_session.add(grade)
    db_session.flush()

    cls1 = Class(school_id=school.id, grade_id=grade.id, code="7-1", name="7-1", student_count=20)
    cls2 = Class(school_id=school.id, grade_id=grade.id, code="7-2", name="7-2", student_count=20)
    db_session.add_all([cls1, cls2])

    subj = Subject(school_id=school.id, code="MATH", name_fr="Math", name_he="מתמטיקה")
    db_session.add(subj)

    t1 = Teacher(school_id=school.id, code="T1", first_name="Alice", last_name="A", languages=["fr"])
    t2 = Teacher(school_id=school.id, code="T2", first_name="Bob", last_name="B", languages=["fr"])
    db_session.add_all([t1, t2])

    r1 = Room(school_id=school.id, code="R1", name="Salle 1", capacity=30)
    r2 = Room(school_id=school.id, code="R2", name="Salle 2", capacity=30)
    db_session.add_all([r1, r2])

    db_session.commit()
    for obj in [school, grade, cls1, cls2, subj, t1, t2, r1, r2]:
        db_session.refresh(obj)

    return {
        "school": school, "grade": grade,
        "classes": [cls1, cls2], "subject": subj,
        "teachers": [t1, t2], "rooms": [r1, r2],
    }


def add_simple_groups(db_session, env: dict, *, hours: int = 2) -> list[Group]:
    """Ajoute 1 group par classe (cours classique)."""
    groups = []
    for i, cls in enumerate(env["classes"]):
        g = Group(
            school_id=env["school"].id, grade_id=env["grade"].id,
            subject_id=env["subject"].id,
            label=f"Math {cls.code}", hours_per_week=hours,
            group_type=GroupType.WHOLE_CLASS,
        )
        g.teachers.append(env["teachers"][i])
        g.source_classes.append(cls)
        db_session.add(g)
        groups.append(g)
    db_session.commit()
    for g in groups:
        db_session.refresh(g)
    return groups


# ---------------------------------------------------------------------------
# Cas succès
# ---------------------------------------------------------------------------

class TestEngineSuccess:
    def test_minimal_generate(self, db_session):
        env = setup_minimal_school(db_session)
        add_simple_groups(db_session, env, hours=2)

        engine = TimetableEngine(db_session, env["school"].id)
        result = engine.generate(schedule_name="Test 1")

        assert isinstance(result, SolveSuccess), f"Expected success, got {type(result).__name__}"
        assert result.placed_entries == 4  # 2 groups × 2h
        assert result.schedule_id is not None
        assert result.solver_time_seconds >= 0

        # Vérifier les ScheduleEntry persistées
        entries = db_session.query(ScheduleEntry).filter_by(schedule_id=result.schedule_id).all()
        assert len(entries) == 4
        for e in entries:
            # Matière sans required_room_type → cours en salle de classe
            # (כיתת אם) → room_id NULL. Seules les matières à salle spéciale
            # (labo, gym) reçoivent une salle du solveur.
            assert e.room_id is None
            assert e.day_of_week in range(5)
            assert e.slot_index in range(4)

    def test_two_teachers_two_classes_no_overlap(self, db_session):
        """Les structurelles teacher/class no-overlap doivent être respectées."""
        env = setup_minimal_school(db_session)
        add_simple_groups(db_session, env, hours=3)

        result = TimetableEngine(db_session, env["school"].id).generate()
        assert isinstance(result, SolveSuccess)

        entries = db_session.query(ScheduleEntry).filter_by(schedule_id=result.schedule_id).all()

        # Vérifier : aucun prof n'enseigne 2 cours en parallèle
        for day in range(5):
            for slot in range(4):
                slot_entries = [e for e in entries if e.day_of_week == day and e.slot_index == slot]
                teachers_here = []
                for e in slot_entries:
                    g = db_session.query(Group).get(e.group_id)
                    teachers_here.extend(t.id for t in g.teachers)
                assert len(teachers_here) == len(set(teachers_here)), \
                    f"Prof en double sur jour {day} créneau {slot}"


# ---------------------------------------------------------------------------
# Cas conflit (INFEASIBLE → MUS)
# ---------------------------------------------------------------------------

class TestEngineConflict:
    def test_too_many_hours_infeasible(self, db_session):
        """Demander plus d'heures que de slots disponibles → INFEASIBLE.
        Le MUS doit pointer vers la contrainte hours_per_week implicite."""
        # 1 jour × 2 slots, mais 1 group à 5h → impossible
        env = setup_minimal_school(db_session, days=1, slots_per_day=2)
        # 1 seule classe pour simplifier
        env["classes"] = env["classes"][:1]
        env["teachers"] = env["teachers"][:1]
        add_simple_groups(db_session, env, hours=5)

        result = TimetableEngine(db_session, env["school"].id).generate(max_time_seconds=5)
        assert isinstance(result, SolveConflict), \
            f"Expected conflict, got {type(result).__name__}: {result}"

        # Le MUS doit contenir au moins un item lié au volume horaire
        types = {c.constraint_type for c in result.conflicts}
        assert "group_hours_per_week" in types, \
            f"Expected group_hours_per_week in conflict, got {types}"

    def test_blocked_teacher_with_required_hours_infeasible(self, db_session):
        """Prof avec 4h à caser, mais bloqué sur 3 jours sur 4 dispos → infaisable.
        Le MUS doit identifier la contrainte BLOCK_SLOT_TEACHER."""
        env = setup_minimal_school(db_session, days=4, slots_per_day=1)
        env["classes"] = env["classes"][:1]
        env["teachers"] = env["teachers"][:1]
        add_simple_groups(db_session, env, hours=4)  # 4h à placer sur 4 slots dispos

        # Bloquer le prof sur 3 jours → reste 1 slot pour 4h
        block = DBConstraint(
            school_id=env["school"].id,
            constraint_type=ConstraintType.BLOCK_SLOT_TEACHER,
            priority=ConstraintPriority.HARD,
            parameters={
                "days": [0, 1, 2],
                "slot_indices": [0],
                "target_id": env["teachers"][0].id,
            },
            origin_role=ConstraintOriginRole.TEACHER,
            origin_description="Prof indisponible 3 jours",
        )
        db_session.add(block)
        db_session.commit()
        db_session.refresh(block)

        result = TimetableEngine(db_session, env["school"].id).generate(max_time_seconds=5)
        assert isinstance(result, SolveConflict)

        # Le MUS doit contenir notre contrainte de blocage (par db_id)
        db_ids = {c.constraint_id for c in result.conflicts}
        assert block.id in db_ids, \
            f"Block constraint {block.id} should be in MUS, got {db_ids}"


# ---------------------------------------------------------------------------
# Cycle dialogue : conflit → relax → success (le test le plus important)
# ---------------------------------------------------------------------------

class TestDialogueCycle:
    def test_relax_conflict_resolves(self, db_session):
        """Scénario UI :
        1. Génère → conflit (contrainte X bloque)
        2. User clique 'relax X'
        3. Re-génère avec disabled_constraint_ids=[X] → succès
        """
        env = setup_minimal_school(db_session, days=4, slots_per_day=1)
        env["classes"] = env["classes"][:1]
        env["teachers"] = env["teachers"][:1]
        add_simple_groups(db_session, env, hours=4)

        block = DBConstraint(
            school_id=env["school"].id,
            constraint_type=ConstraintType.BLOCK_SLOT_TEACHER,
            priority=ConstraintPriority.HARD,
            parameters={
                "days": [0, 1, 2],
                "slot_indices": [0],
                "target_id": env["teachers"][0].id,
            },
            origin_role=ConstraintOriginRole.TEACHER,
        )
        db_session.add(block)
        db_session.commit()
        db_session.refresh(block)

        engine = TimetableEngine(db_session, env["school"].id)

        # Étape 1 : conflit
        r1 = engine.generate(max_time_seconds=5)
        assert isinstance(r1, SolveConflict)
        assert block.id in {c.constraint_id for c in r1.conflicts}

        # Étape 2 : l'utilisateur choisit de relaxer le block → re-solve
        # (besoin d'un nouveau engine car l'ancien a son état literal/MUS pollué)
        engine2 = TimetableEngine(db_session, env["school"].id)
        r2 = engine2.generate(
            schedule_name="After relax",
            disabled_constraint_ids=[block.id],
            max_time_seconds=5,
        )
        assert isinstance(r2, SolveSuccess), f"Expected success after relax, got {r2}"
        assert r2.placed_entries == 4
        assert block.id in r2.relaxed_constraint_ids


# ---------------------------------------------------------------------------
# Barrette : ParallelCohort doit être respectée dans la solution
# ---------------------------------------------------------------------------

class TestBarretteIntegration:
    def test_barrette_with_shared_source_classes(self, db_session):
        """REGRESSION : Math fort & Math normal partagent les MÊMES source_classes
        (les élèves d'une שכבה sont dispatchés entre niveaux). Sans la finesse
        "1 représentant par cohorte" dans ClassNoOverlap, c'est infaisable."""
        env = setup_minimal_school(db_session, days=2, slots_per_day=3)

        cohort = ParallelCohort(
            school_id=env["school"].id, grade_id=env["grade"].id,
            label="Math barrette",
        )
        db_session.add(cohort)
        db_session.flush()

        groups = []
        for i, hours in enumerate([2, 2]):
            g = Group(
                school_id=env["school"].id, grade_id=env["grade"].id,
                subject_id=env["subject"].id,
                label=f"Math niv {i}", hours_per_week=hours,
                group_type=GroupType.LEVEL_GROUP, parallel_cohort_id=cohort.id,
            )
            g.teachers.append(env["teachers"][i])
            # POINT-CLÉ : les 2 groupes ont les MÊMES source_classes
            g.source_classes.extend(env["classes"])
            db_session.add(g)
            groups.append(g)
        db_session.commit()

        result = TimetableEngine(db_session, env["school"].id).generate(max_time_seconds=5)
        assert isinstance(result, SolveSuccess), \
            f"Barrette à source_classes partagées doit être faisable, got {result}"
        assert result.placed_entries == 4

    def test_parallel_cohort_groups_at_same_slot(self, db_session):
        """Math 5 yehidot + Math 3 yehidot dans la même cohorte : doivent être
        au même créneau dans la solution."""
        env = setup_minimal_school(db_session, days=3, slots_per_day=4)

        cohort = ParallelCohort(
            school_id=env["school"].id, grade_id=env["grade"].id,
            label="Math barrette ז",
        )
        db_session.add(cohort)
        db_session.flush()

        # 2 groups, même hours, dans la cohorte, profs différents
        groups = []
        for i, hours in enumerate([2, 2]):
            g = Group(
                school_id=env["school"].id, grade_id=env["grade"].id,
                subject_id=env["subject"].id,
                label=f"Math niveau {i}", hours_per_week=hours,
                group_type=GroupType.LEVEL_GROUP,
                parallel_cohort_id=cohort.id,
            )
            g.teachers.append(env["teachers"][i])
            # Les 2 groupes recrutent des élèves d'UNE seule classe (sinon class no-overlap fâché)
            g.source_classes.append(env["classes"][i])
            db_session.add(g)
            groups.append(g)
        db_session.commit()
        for g in groups:
            db_session.refresh(g)

        result = TimetableEngine(db_session, env["school"].id).generate(max_time_seconds=5)
        assert isinstance(result, SolveSuccess)

        entries = db_session.query(ScheduleEntry).filter_by(schedule_id=result.schedule_id).all()
        # Regrouper par (day, slot) — les 2 groups de la cohorte doivent toujours être ensemble
        by_slot: dict[tuple[int, int], set[int]] = {}
        for e in entries:
            by_slot.setdefault((e.day_of_week, e.slot_index), set()).add(e.group_id)

        for slot, g_ids in by_slot.items():
            # Si UN groupe de la cohorte est posé sur ce slot, l'autre aussi
            cohort_groups_here = g_ids & {g.id for g in groups}
            if cohort_groups_here:
                assert len(cohort_groups_here) == len(groups), \
                    f"Cohorte non synchronisée sur {slot} : {cohort_groups_here}"


# ---------------------------------------------------------------------------
# Multi-tenant : isolation entre écoles
# ---------------------------------------------------------------------------

class TestMultiTenant:
    def test_engine_only_sees_its_school(self, db_session):
        """Engine d'école A ignore complètement les données de l'école B."""
        env_a = setup_minimal_school(db_session)
        env_a["school"].code = "a"
        env_a["school"].name = "A"
        db_session.commit()
        add_simple_groups(db_session, env_a, hours=2)

        # School B avec une autre config + des groupes "piège" qui seraient
        # impossibles à caser si l'engine A les voyait
        b = School(code="b", name="B")
        db_session.add(b)
        db_session.flush()
        # B n'a aucun time_slot — donc impossible de placer quoi que ce soit chez B
        grade_b = Grade(school_id=b.id, code="X", name="X", order=1,
                        grouping_policy=GroupingPolicy.CLASS_CENTRIC)
        db_session.add(grade_b)
        db_session.flush()
        cls_b = Class(school_id=b.id, grade_id=grade_b.id, code="X-1", name="X-1", student_count=99)
        subj_b = Subject(school_id=b.id, code="X", name_fr="X", name_he="X")
        teach_b = Teacher(school_id=b.id, code="X", first_name="X", last_name="X", languages=["fr"])
        db_session.add_all([cls_b, subj_b, teach_b])
        db_session.flush()
        g_b = Group(school_id=b.id, grade_id=grade_b.id, subject_id=subj_b.id,
                    label="Impossible", hours_per_week=99)
        g_b.teachers.append(teach_b)
        g_b.source_classes.append(cls_b)
        db_session.add(g_b)
        db_session.commit()

        # Engine A doit réussir, sans se soucier des données B
        result = TimetableEngine(db_session, env_a["school"].id).generate()
        assert isinstance(result, SolveSuccess), \
            f"Engine A leaked into school B data; got {type(result).__name__}"

        # Le schedule A ne contient que des groupes A
        entries = db_session.query(ScheduleEntry).filter_by(schedule_id=result.schedule_id).all()
        a_group_ids = {g.id for g in db_session.query(Group).filter_by(school_id=env_a["school"].id)}
        for e in entries:
            assert e.group_id in a_group_ids


# ---------------------------------------------------------------------------
# Objectifs qualité (école israélienne)
# ---------------------------------------------------------------------------

class TestQualityObjectives:
    def test_class_compactness_no_gaps(self, db_session):
        """2 cours d'1h pour la même classe, 1 jour de 4 créneaux → l'objectif
        de compacité doit les placer sur des créneaux ADJACENTS (pas de חלון)."""
        env = setup_minimal_school(db_session, days=1, slots_per_day=4)
        env["classes"] = env["classes"][:1]
        cls = env["classes"][0]

        for i in range(2):
            g = Group(
                school_id=env["school"].id, grade_id=env["grade"].id,
                subject_id=env["subject"].id,
                label=f"Cours {i}", hours_per_week=1,
                group_type=GroupType.WHOLE_CLASS,
            )
            g.teachers.append(env["teachers"][i])
            g.source_classes.append(cls)
            db_session.add(g)
        db_session.commit()

        result = TimetableEngine(db_session, env["school"].id).generate(max_time_seconds=10)
        assert isinstance(result, SolveSuccess)

        entries = db_session.query(ScheduleEntry).filter_by(schedule_id=result.schedule_id).all()
        slots = sorted(e.slot_index for e in entries)
        assert len(slots) == 2
        assert slots[1] - slots[0] == 1, \
            f"Compacité violée : créneaux {slots} devraient être adjacents"

    def test_subject_spread_over_days(self, db_session):
        """Un group de 2h avec 2 jours disponibles → l'étalement doit répartir
        1h par jour (pas 2h le même jour)."""
        env = setup_minimal_school(db_session, days=2, slots_per_day=3)
        env["classes"] = env["classes"][:1]
        env["teachers"] = env["teachers"][:1]
        add_simple_groups(db_session, env, hours=2)

        result = TimetableEngine(db_session, env["school"].id).generate(max_time_seconds=10)
        assert isinstance(result, SolveSuccess)

        entries = db_session.query(ScheduleEntry).filter_by(schedule_id=result.schedule_id).all()
        days = sorted(e.day_of_week for e in entries)
        assert days == [0, 1], f"Étalement violé : les 2h sont sur les jours {days}"

    def test_special_room_still_assigned(self, db_session):
        """Une matière avec required_room_type doit recevoir une salle du bon type."""
        env = setup_minimal_school(db_session, days=2, slots_per_day=3)
        lab = Room(school_id=env["school"].id, code="LAB", name="Labo",
                   capacity=24, room_type="lab")
        db_session.add(lab)
        subj_sci = Subject(school_id=env["school"].id, code="SCI",
                            name_fr="Sciences", name_he="מדעים",
                            required_room_type="lab")
        db_session.add(subj_sci)
        db_session.flush()

        g = Group(
            school_id=env["school"].id, grade_id=env["grade"].id,
            subject_id=subj_sci.id, label="Sciences",
            hours_per_week=2, group_type=GroupType.WHOLE_CLASS,
        )
        g.teachers.append(env["teachers"][0])
        g.source_classes.append(env["classes"][0])
        db_session.add(g)
        db_session.commit()
        db_session.refresh(lab)

        result = TimetableEngine(db_session, env["school"].id).generate(max_time_seconds=10)
        assert isinstance(result, SolveSuccess)

        entries = db_session.query(ScheduleEntry).filter_by(schedule_id=result.schedule_id).all()
        assert len(entries) == 2
        for e in entries:
            assert e.room_id == lab.id, "La matière labo doit être dans le labo"
