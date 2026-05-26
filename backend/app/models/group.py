"""Group — unité d'enseignement réelle planifiée par le solveur.

C'est la PIÈCE MAÎTRESSE du modèle. Un Group représente UN cours qui sera
placé dans un créneau. Caractéristiques clés :

- Un Group a un Subject et 1+ Teachers (co-enseignement, ou sous-sections
  d'un même créneau parallèle — voir la doc iscool dans la mémoire).
- Un Group recrute ses élèves depuis 1+ Classes (Class M2M source_classes) :
  - Un seul Class → cours classique (classe entière)
  - Plusieurs Classes → barrette/הקבצה inter-classes au sein d'un Grade
- Un Group peut appartenir à une ParallelCohort : tous les Groups d'une
  cohorte doivent être au même créneau (math 5/4/3 yehidot par ex.).

Le solveur place des Groups dans (day, slot, room). La vue "emploi du temps
de la classe X" est dérivée : tous les Groups dont source_classes contient X.
"""

import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base_mixin import TimestampMixin


class GroupType(str, enum.Enum):
    """Origine logique du Group (informationnel, pour l'UI/admin).

    Le solveur ne distingue pas — il voit juste des Groups avec source_classes.
    """
    WHOLE_CLASS = "whole_class"        # Toute la classe (cours classique)
    LEVEL_GROUP = "level_group"        # Niveau (yehidot, חזק/בינוני/חלש)
    OPTION_GROUP = "option_group"      # Option (espagnol vs arabe)
    GENDER_GROUP = "gender_group"      # Séparation filles/garçons
    SPLIT_GROUP = "split_group"        # Dédoublement TP (moitié de classe)


class Group(Base, TimestampMixin):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    grade_id = Column(Integer, ForeignKey("grades.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    parallel_cohort_id = Column(Integer, ForeignKey("parallel_cohorts.id", ondelete="SET NULL"), nullable=True, index=True)

    group_type = Column(Enum(GroupType), nullable=False, default=GroupType.WHOLE_CLASS)
    label = Column(String(200), nullable=False)            # ex: "Math 5 yehidot - ז"
    hours_per_week = Column(Integer, nullable=False, default=1)
    student_count = Column(Integer, nullable=True)         # nullable car déductible

    school = relationship("School", back_populates="groups")
    grade = relationship("Grade", back_populates="groups")
    subject = relationship("Subject", back_populates="groups")
    parallel_cohort = relationship("ParallelCohort", back_populates="groups")

    teachers = relationship("Teacher", secondary="group_teachers", back_populates="groups")
    source_classes = relationship("Class", secondary="group_source_classes", back_populates="groups")
    schedule_entries = relationship("ScheduleEntry", back_populates="group", cascade="all, delete-orphan")


class ParallelCohort(Base, TimestampMixin):
    """Ensemble de Groups qui DOIVENT être planifiés au même créneau.

    Cas d'usage typiques :
    - Barrette math שכבה ז : Groups [Math 5 ז, Math 4 ז, Math 3 ז] → 1 cohorte
    - Barrette options : Groups [Espagnol 10e, Arabe 10e] → 1 cohorte
    - Tracks tech lycée : [Élec, Info, Physique, Telecom] → 1 cohorte

    Si les hours_per_week diffèrent au sein de la cohorte, les heures
    supplémentaires (groupes "plus long") sont gérées via une contrainte
    `EXTRA_HOURS_AT_DAY_EDGE` (cf. catalogue).
    """
    __tablename__ = "parallel_cohorts"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    grade_id = Column(Integer, ForeignKey("grades.id", ondelete="CASCADE"), nullable=True, index=True)
    label = Column(String(200), nullable=False)            # ex: "Math שכבה ז"

    school = relationship("School", back_populates="parallel_cohorts")
    grade = relationship("Grade", back_populates="parallel_cohorts")
    groups = relationship("Group", back_populates="parallel_cohort")
