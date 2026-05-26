"""Tests des modèles SQLAlchemy v2.

Couverture :
- Création / persistence basique de chaque entité
- Contraintes d'unicité (multi-tenant scoping)
- Relations many-to-many (Group ↔ Teachers, Group ↔ Classes)
- Cascade delete (suppression d'une School purge ses entités)
- Isolation multi-école (codes peuvent être identiques entre 2 schools)
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    Class,
    Constraint,
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
    ScheduleStatus,
    School,
    Subject,
    Teacher,
    TimeSlot,
    User,
    UserRole,
)


# ---------------------------------------------------------------------------
# School + multi-tenant
# ---------------------------------------------------------------------------

class TestSchool:
    def test_create_school(self, db_session):
        s = School(code="my-school", name="Mon école")
        db_session.add(s)
        db_session.commit()
        assert s.id is not None
        assert s.is_active is True
        assert s.default_language == "fr"

    def test_school_code_unique(self, db_session):
        db_session.add(School(code="dup", name="A"))
        db_session.commit()
        db_session.add(School(code="dup", name="B"))
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_two_schools_can_have_same_entity_codes(self, db_session, school, another_school):
        """Multi-tenant : code "T1" peut exister dans 2 écoles différentes."""
        db_session.add(Teacher(school_id=school.id, code="T1", first_name="A", last_name="A"))
        db_session.add(Teacher(school_id=another_school.id, code="T1", first_name="B", last_name="B"))
        db_session.commit()  # ne doit PAS lever — uniqueness est (school_id, code)


# ---------------------------------------------------------------------------
# Grade / Class
# ---------------------------------------------------------------------------

class TestGradeAndClass:
    def test_create_grade(self, db_session, school):
        g = Grade(school_id=school.id, code="7", name="7e", order=7)
        db_session.add(g)
        db_session.commit()
        assert g.grouping_policy == GroupingPolicy.CLASS_CENTRIC

    def test_class_belongs_to_grade(self, db_session, school):
        g = Grade(school_id=school.id, code="7", name="7e", order=7)
        db_session.add(g)
        db_session.commit()
        c = Class(school_id=school.id, grade_id=g.id, code="7-1", name="7-1", student_count=25)
        db_session.add(c)
        db_session.commit()
        assert c.grade.code == "7"
        assert g.classes[0].code == "7-1"


# ---------------------------------------------------------------------------
# Group : multi-prof + multi-class (pièce maîtresse)
# ---------------------------------------------------------------------------

class TestGroup:
    def test_group_with_one_teacher_one_class(self, db_session, sample_school_data, school):
        d = sample_school_data
        g = Group(
            school_id=school.id, grade_id=d["grade"].id, subject_id=d["subjects"][0].id,
            label="Math 7-1 classique", hours_per_week=4,
            group_type=GroupType.WHOLE_CLASS,
        )
        g.teachers.append(d["teachers"][0])
        g.source_classes.append(d["classes"][0])
        db_session.add(g)
        db_session.commit()

        assert len(g.teachers) == 1
        assert len(g.source_classes) == 1
        assert d["classes"][0].groups[0].id == g.id

    def test_group_with_multiple_teachers(self, db_session, sample_school_data, school):
        """Cas iscool : 5 profs sur un créneau math = 5 sous-groupes de niveau.
        Dans notre modèle, on aurait 5 Groups séparés. Mais on supporte aussi
        N profs sur 1 Group (co-enseignement)."""
        d = sample_school_data
        g = Group(
            school_id=school.id, grade_id=d["grade"].id, subject_id=d["subjects"][1].id,
            label="Hébreu co-enseignement", hours_per_week=3,
        )
        g.teachers.extend(d["teachers"])  # 3 profs
        g.source_classes.append(d["classes"][0])
        db_session.add(g)
        db_session.commit()
        assert len(g.teachers) == 3

    def test_group_with_multiple_source_classes_barrette(self, db_session, sample_school_data, school):
        """Barrette inter-classes : un Group sert plusieurs Classes (modèle iscool)."""
        d = sample_school_data
        g = Group(
            school_id=school.id, grade_id=d["grade"].id, subject_id=d["subjects"][0].id,
            label="Math 5 yehidot - שכבה ז", hours_per_week=5,
            group_type=GroupType.LEVEL_GROUP,
        )
        g.teachers.append(d["teachers"][0])
        g.source_classes.extend(d["classes"])  # 7-1 et 7-2
        db_session.add(g)
        db_session.commit()

        # Les 2 classes ont accès à ce group
        for c in d["classes"]:
            db_session.refresh(c)
            assert g.id in [grp.id for grp in c.groups]


# ---------------------------------------------------------------------------
# ParallelCohort : math 5/4/3 yehidot doivent être au même créneau
# ---------------------------------------------------------------------------

class TestParallelCohort:
    def test_cohort_groups_relationship(self, db_session, sample_school_data, school):
        d = sample_school_data
        cohort = ParallelCohort(school_id=school.id, grade_id=d["grade"].id,
                                label="Math שכבה ז")
        db_session.add(cohort)
        db_session.commit()

        # 3 groups dans la cohorte
        for i, hours in enumerate([5, 4, 3], start=1):
            g = Group(
                school_id=school.id, grade_id=d["grade"].id, subject_id=d["subjects"][0].id,
                label=f"Math {hours} yehidot", hours_per_week=hours,
                group_type=GroupType.LEVEL_GROUP, parallel_cohort_id=cohort.id,
            )
            g.teachers.append(d["teachers"][i - 1])
            g.source_classes.extend(d["classes"])
            db_session.add(g)
        db_session.commit()
        db_session.refresh(cohort)

        assert len(cohort.groups) == 3
        # Et chaque group connaît sa cohorte
        for g in cohort.groups:
            assert g.parallel_cohort_id == cohort.id


# ---------------------------------------------------------------------------
# Constraint : table unifiée polymorphe
# ---------------------------------------------------------------------------

class TestConstraint:
    def test_create_block_slot_teacher_constraint(self, db_session, sample_school_data, school):
        d = sample_school_data
        c = Constraint(
            school_id=school.id,
            constraint_type=ConstraintType.BLOCK_SLOT_TEACHER,
            priority=ConstraintPriority.HARD,
            parameters={"days": [1], "slot_indices": [0, 1], "target_id": d["teachers"][0].id},
            origin_role=ConstraintOriginRole.TEACHER,
            origin_description="Sarah Cohen indispo lundi matin",
        )
        db_session.add(c)
        db_session.commit()

        loaded = db_session.query(Constraint).filter_by(id=c.id).one()
        assert loaded.constraint_type == ConstraintType.BLOCK_SLOT_TEACHER
        assert loaded.parameters["target_id"] == d["teachers"][0].id
        assert loaded.is_active is True


# ---------------------------------------------------------------------------
# Schedule + ScheduleEntry : entries rattachées à Group (pas Class)
# ---------------------------------------------------------------------------

class TestSchedule:
    def test_entry_references_group_not_class(self, db_session, sample_school_data, school):
        """ScheduleEntry.group_id existe, pas de class_id direct."""
        d = sample_school_data
        g = Group(
            school_id=school.id, grade_id=d["grade"].id, subject_id=d["subjects"][0].id,
            label="Test", hours_per_week=1,
        )
        g.teachers.append(d["teachers"][0])
        g.source_classes.append(d["classes"][0])
        db_session.add(g)
        db_session.commit()

        sched = Schedule(school_id=school.id, name="Test sched")
        db_session.add(sched)
        db_session.commit()

        entry = ScheduleEntry(
            schedule_id=sched.id, group_id=g.id, room_id=d["rooms"][0].id,
            day_of_week=0, slot_index=1,
        )
        db_session.add(entry)
        db_session.commit()

        # Vérif relation
        assert entry.group.label == "Test"
        # Et pas d'attribut class_id (architecture: le schedule "de la classe" est dérivé)
        assert not hasattr(entry, "class_id")


# ---------------------------------------------------------------------------
# Cascade delete : supprimer School purge tout
# ---------------------------------------------------------------------------

class TestCascade:
    def test_delete_school_cascades(self, db_session, sample_school_data, school):
        d = sample_school_data
        # Quelques entités
        assert db_session.query(Class).count() == 2
        assert db_session.query(Teacher).count() == 3

        db_session.delete(school)
        db_session.commit()

        # Tout doit être vide
        assert db_session.query(Class).count() == 0
        assert db_session.query(Teacher).count() == 0
        assert db_session.query(Subject).count() == 0
        assert db_session.query(Room).count() == 0
        assert db_session.query(Grade).count() == 0
        assert db_session.query(TimeSlot).count() == 0
