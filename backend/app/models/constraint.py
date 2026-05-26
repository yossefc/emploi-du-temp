"""Constraint — modèle UNIFIÉ de toutes les contraintes du solveur.

Plutôt que 5 tables distinctes (TeacherAvailability, RoomUnavailability, …),
on a une seule table polymorphe `constraints` avec :
  - `constraint_type` : identifie le type (cf. ConstraintType enum)
  - `priority` : HARD / SOFT
  - `weight` : pour les SOFT, importance relative
  - `parameters` : JSON, schéma dépendant du type
  - `origin_*` : qui a posé la contrainte (pour le dialogue de conflit)

Le moteur de contraintes (Phase 2) lit cette table et instancie l'objet
Python correspondant via un registry `CONSTRAINT_REGISTRY[constraint_type]`.

Voir le catalogue dans la mémoire `school-amit-bar-ilan-netanya` et la doc
Phase 0 dans la conversation.
"""

import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, JSON, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base_mixin import TimestampMixin


class ConstraintPriority(str, enum.Enum):
    HARD = "hard"      # Doit être satisfaite. Si infaisable → dialogue avec user.
    SOFT = "soft"      # Devrait être satisfaite. Pondérée. Auto-relaxable.


class ConstraintType(str, enum.Enum):
    """Catalogue des types de contraintes supportées par le solveur.

    NOTE : chaque type définit son schéma de `parameters` JSON. Ce schéma est
    documenté dans la classe Python correspondante du module `app.solver.constraints`.
    """

    # --- Structurelles (toujours actives, jamais relaxables) ---
    # Pas stockées en DB : ajoutées par défaut par le builder.

    # --- Blocages ---
    BLOCK_SLOT_SCHOOL = "block_slot_school"          # ex: prière, fermeture
    BLOCK_SLOT_CLASS = "block_slot_class"            # ex: sortie scolaire
    BLOCK_SLOT_GROUP = "block_slot_group"            # ex: groupe en stage
    BLOCK_SLOT_TEACHER = "block_slot_teacher"        # indisponibilité prof
    BLOCK_SLOT_ROOM = "block_slot_room"              # salle en travaux

    # --- Placement matière ---
    SUBJECT_REQUIRED_SLOT_RANGE = "subject_required_slot_range"
    SUBJECT_PREFERRED_SLOT_RANGE = "subject_preferred_slot_range"
    SUBJECT_REQUIRES_ROOM_TYPE = "subject_requires_room_type"
    SUBJECT_CONSECUTIVE_HOURS = "subject_consecutive_hours"
    SUBJECT_NOT_CONSECUTIVE_DAYS = "subject_not_consecutive_days"
    SUBJECT_MAX_PER_DAY = "subject_max_per_day"

    # --- Volumes ---
    GROUP_HOURS_PER_WEEK = "group_hours_per_week"
    TEACHER_MAX_HOURS_WEEK = "teacher_max_hours_week"
    TEACHER_MAX_HOURS_DAY = "teacher_max_hours_day"
    TEACHER_MAX_CONSECUTIVE = "teacher_max_consecutive"
    TEACHER_MIN_BREAK_AFTER = "teacher_min_break_after"

    # --- Affectation ---
    TEACHER_QUALIFIED_FOR_SUBJECT = "teacher_qualified_for_subject"
    TEACHER_LANGUAGE_REQUIRED = "teacher_language_required"
    TEACHERS_MUST_TEACH_TOGETHER = "teachers_must_teach_together"  # co-enseignement

    # --- Spécifique barrette ---
    EXTRA_HOURS_AT_DAY_EDGE = "extra_hours_at_day_edge"

    # --- (v2) Préférences profs pondérées ---
    TEACHER_PREFER_MORNING = "teacher_prefer_morning"
    TEACHER_PREFER_AFTERNOON = "teacher_prefer_afternoon"
    TEACHER_AVOID_GAPS = "teacher_avoid_gaps"
    TEACHER_PREFER_GROUPED_DAYS = "teacher_prefer_grouped_days"


class ConstraintOriginRole(str, enum.Enum):
    """Qui a posé la contrainte (pour le dialogue de conflit)."""
    SYSTEM = "system"                  # générée par seed / défaut
    SCHOOL_ADMIN = "school_admin"      # admin école
    TEACHER = "teacher"                # prof a posé une contrainte le concernant
    AI_PARSED = "ai_parsed"            # parsée par IA depuis langage naturel


class Constraint(Base, TimestampMixin):
    __tablename__ = "constraints"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    constraint_type = Column(Enum(ConstraintType), nullable=False, index=True)
    priority = Column(Enum(ConstraintPriority), nullable=False, default=ConstraintPriority.HARD)
    weight = Column(Integer, nullable=True)                # pour SOFT : 1-100

    parameters = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)

    # --- Origine (pour le dialogue de résolution de conflit) ---
    origin_role = Column(Enum(ConstraintOriginRole), nullable=False, default=ConstraintOriginRole.SCHOOL_ADMIN)
    origin_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    origin_description = Column(Text, nullable=True)       # explication libre, affichée à l'utilisateur
    origin_raw_text = Column(Text, nullable=True)          # texte original si AI_PARSED

    school = relationship("School", back_populates="constraints")
    origin_user = relationship("User", foreign_keys=[origin_user_id])
