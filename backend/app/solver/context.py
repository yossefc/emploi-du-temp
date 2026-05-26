"""SolverContext — état partagé entre toutes les contraintes pendant la construction du modèle CP-SAT.

Chaque contrainte reçoit ce contexte dans `apply(ctx)` et y trouve :
- Le modèle CP-SAT (`ctx.model`)
- Les données métier (groups, teachers, classes, rooms, time_slots, parallel_cohorts)
- Les variables de décision (`ctx.assigned`, `ctx.room_used`)
- Des helpers (créneaux actifs un jour, groupes d'un prof, etc.)

Le contexte est construit par l'engine (Phase 3) avant d'appliquer les contraintes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ortools.sat.python import cp_model

from app.models import (
    Class,
    Group,
    ParallelCohort,
    Room,
    School,
    Teacher,
    TimeSlot,
)


# Une "position de placement" = (day_of_week, slot_index)
Slot = tuple[int, int]


@dataclass
class SolverContext:
    """État du builder CP-SAT.

    Conventions de variables :
    - `assigned[group_id][(day, slot)]` : BoolVar = 1 si group occupe ce créneau
    - `room_used[group_id][(day, slot)][room_id]` : BoolVar = 1 si group utilise cette salle à ce créneau
      (créé uniquement pour les (g, s) où la salle est candidate)
    """

    # --- Modèle CP-SAT ---
    model: cp_model.CpModel

    # --- Données métier ---
    school: School
    groups: list[Group]
    teachers: list[Teacher]
    classes: list[Class]
    rooms: list[Room]
    time_slots: list[TimeSlot]
    parallel_cohorts: list[ParallelCohort]

    # --- Variables de décision ---
    # group_id -> { (day, slot) -> BoolVar }
    assigned: dict[int, dict[Slot, cp_model.IntVar]] = field(default_factory=dict)
    # group_id -> { (day, slot) -> { room_id -> BoolVar } }
    room_used: dict[int, dict[Slot, dict[int, cp_model.IntVar]]] = field(default_factory=dict)

    # --- Caches dérivés ---
    _slots_by_day: dict[int, list[int]] = field(default_factory=dict, repr=False)
    _groups_by_teacher: dict[int, list[int]] = field(default_factory=dict, repr=False)
    _groups_by_class: dict[int, list[int]] = field(default_factory=dict, repr=False)
    _group_by_id: dict[int, Group] = field(default_factory=dict, repr=False)
    _teacher_by_id: dict[int, Teacher] = field(default_factory=dict, repr=False)
    _room_by_id: dict[int, Room] = field(default_factory=dict, repr=False)

    def build_caches(self) -> None:
        """À appeler une fois après chargement des données."""
        self._group_by_id = {g.id: g for g in self.groups}
        self._teacher_by_id = {t.id: t for t in self.teachers}
        self._room_by_id = {r.id: r for r in self.rooms}

        self._slots_by_day = {}
        for ts in self.time_slots:
            if ts.is_active and not ts.is_break:
                self._slots_by_day.setdefault(ts.day_of_week, []).append(ts.slot_index)
        for day in self._slots_by_day:
            self._slots_by_day[day].sort()

        self._groups_by_teacher = {}
        self._groups_by_class = {}
        for g in self.groups:
            for t in g.teachers:
                self._groups_by_teacher.setdefault(t.id, []).append(g.id)
            for c in g.source_classes:
                self._groups_by_class.setdefault(c.id, []).append(g.id)

    # --- Helpers ---
    def active_slots(self, day: int) -> list[int]:
        """Indices des créneaux non-pause activés ce jour."""
        return self._slots_by_day.get(day, [])

    def all_active_positions(self) -> list[Slot]:
        """Toutes les positions (day, slot) où un cours peut être placé."""
        return [(d, s) for d, slots in self._slots_by_day.items() for s in slots]

    def active_days(self) -> list[int]:
        return sorted(self._slots_by_day.keys())

    def group(self, group_id: int) -> Group:
        return self._group_by_id[group_id]

    def teacher(self, teacher_id: int) -> Teacher:
        return self._teacher_by_id[teacher_id]

    def room(self, room_id: int) -> Optional[Room]:
        return self._room_by_id.get(room_id)

    def groups_of_teacher(self, teacher_id: int) -> list[int]:
        return self._groups_by_teacher.get(teacher_id, [])

    def groups_of_class(self, class_id: int) -> list[int]:
        return self._groups_by_class.get(class_id, [])

    def compatible_rooms(self, group_id: int) -> list[Room]:
        """Rooms compatibles avec le subject d'un Group (basé sur required_room_type)."""
        g = self.group(group_id)
        req = g.subject.required_room_type
        if not req:
            return [r for r in self.rooms if r.is_active]
        return [r for r in self.rooms if r.is_active and r.room_type == req]
