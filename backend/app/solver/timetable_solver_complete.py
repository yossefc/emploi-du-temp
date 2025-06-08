"""
Timetable solver using Google OR-Tools CP-SAT (complete version).
"""

from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from ortools.sat.python import cp_model
import logging
from datetime import datetime
from collections import defaultdict

from app.models.teacher import Teacher
from app.models.subject import Subject
from app.models.class_group import ClassGroup
from app.models.room import Room
from app.models.constraint import TeacherAvailability, RoomUnavailability, ClassSubjectRequirement

logger = logging.getLogger(__name__)

# Constantes pour les jours et périodes
DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']
PERIODS_PER_DAY = 8
FRIDAY_MAX_PERIOD = 6  # Vendredi se termine à la période 6 (13h)


class TimetableSolver:
    """Complete timetable solver using CP-SAT."""
    
    def __init__(self, db: Session):
        self.db = db
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # Variables de décision
        self.assignments = {}  # (class, day, period, teacher, subject, room) -> BoolVar
        
        # Données du problème
        self.teachers = []
        self.subjects = []
        self.classes = []
        self.rooms = []
        self.requirements = {}  # (class, subject) -> hours_per_week
        self.teacher_subjects = {}  # teacher -> [subjects]
        self.teacher_availability = {}  # (teacher, day, period) -> bool
        self.room_availability = {}  # (room, day, period) -> bool
        
        logger.info("TimetableSolver initialized")
    
    def load_data(self):
        """Charger toutes les données depuis la base de données."""
        logger.info("Loading data from database...")
        
        # Charger les enseignants
        self.teachers = self.db.query(Teacher).filter(Teacher.is_active == True).all()
        logger.info(f"Loaded {len(self.teachers)} teachers")
        
        # Charger les matières
        self.subjects = self.db.query(Subject).filter(Subject.is_active == True).all()
        logger.info(f"Loaded {len(self.subjects)} subjects")
        
        # Charger les classes
        self.classes = self.db.query(ClassGroup).filter(ClassGroup.is_active == True).all()
        logger.info(f"Loaded {len(self.classes)} classes")
        
        # Charger les salles
        self.rooms = self.db.query(Room).filter(Room.is_active == True).all()
        logger.info(f"Loaded {len(self.rooms)} rooms")
        
        # Charger les relations enseignant-matière
        for teacher in self.teachers:
            self.teacher_subjects[teacher.id] = [s.id for s in teacher.subjects]
        
        # Charger les besoins en heures par classe et matière
        requirements = self.db.query(ClassSubjectRequirement).all()
        for req in requirements:
            self.requirements[(req.class_id, req.subject_id)] = req.hours_per_week
        
        # Charger les disponibilités des enseignants
        availabilities = self.db.query(TeacherAvailability).all()
        # Initialiser toutes les disponibilités à True
        for teacher in self.teachers:
            for day_idx, day in enumerate(DAYS):
                for period in range(PERIODS_PER_DAY):
                    self.teacher_availability[(teacher.id, day_idx, period)] = True
        
        # Appliquer les indisponibilités
        for avail in availabilities:
            if not avail.is_available:
                day_idx = DAYS.index(avail.day)
                # Convertir les heures en périodes
                start_period = self._time_to_period(avail.start_time)
                end_period = self._time_to_period(avail.end_time)
                for period in range(start_period, end_period):
                    self.teacher_availability[(avail.teacher_id, day_idx, period)] = False
        
        # Charger les disponibilités des salles
        room_unavails = self.db.query(RoomUnavailability).all()
        # Initialiser toutes les disponibilités à True
        for room in self.rooms:
            for day_idx, day in enumerate(DAYS):
                for period in range(PERIODS_PER_DAY):
                    self.room_availability[(room.id, day_idx, period)] = True
        
        # Appliquer les indisponibilités
        for unavail in room_unavails:
            day_idx = DAYS.index(unavail.day)
            start_period = self._time_to_period(unavail.start_time)
            end_period = self._time_to_period(unavail.end_time)
            for period in range(start_period, end_period):
                self.room_availability[(unavail.room_id, day_idx, period)] = False
    
    def _time_to_period(self, time_str: str) -> int:
        """Convertir une heure (HH:MM) en numéro de période."""
        hour, minute = map(int, time_str.split(':'))
        # Période 0: 8h00-8h45, Période 1: 8h50-9h35, etc.
        if hour < 8:
            return 0
        return min((hour - 8) * 2 + (1 if minute >= 45 else 0), PERIODS_PER_DAY - 1)
    
    def build_model(self):
        """Construire le modèle CP-SAT avec toutes les variables et contraintes."""
        logger.info("Building CP-SAT model...")
        
        # Créer les variables de décision
        for class_group in self.classes:
            for day_idx in range(len(DAYS)):
                max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                for period in range(max_period):
                    for teacher in self.teachers:
                        for subject in self.subjects:
                            # Vérifier si l'enseignant peut enseigner cette matière
                            if subject.id not in self.teacher_subjects.get(teacher.id, []):
                                continue
                            
                            for room in self.rooms:
                                # Vérifier la capacité de la salle
                                if room.capacity < class_group.student_count:
                                    continue
                                
                                # Vérifier le type de salle pour la matière
                                if subject.room_type and room.type != subject.room_type:
                                    continue
                                
                                var_name = f"assign_c{class_group.id}_d{day_idx}_p{period}_t{teacher.id}_s{subject.id}_r{room.id}"
                                var = self.model.NewBoolVar(var_name)
                                self.assignments[(class_group.id, day_idx, period, teacher.id, subject.id, room.id)] = var
        
        logger.info(f"Created {len(self.assignments)} assignment variables")
        
        # Contrainte 1: Une classe ne peut avoir qu'un cours à la fois
        for class_group in self.classes:
            for day_idx in range(len(DAYS)):
                max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                for period in range(max_period):
                    assignments_for_slot = []
                    for key, var in self.assignments.items():
                        if key[0] == class_group.id and key[1] == day_idx and key[2] == period:
                            assignments_for_slot.append(var)
                    
                    if assignments_for_slot:
                        self.model.Add(sum(assignments_for_slot) <= 1)
        
        # Contrainte 2: Un enseignant ne peut enseigner qu'à un endroit à la fois
        for teacher in self.teachers:
            for day_idx in range(len(DAYS)):
                max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                for period in range(max_period):
                    assignments_for_slot = []
                    for key, var in self.assignments.items():
                        if key[3] == teacher.id and key[1] == day_idx and key[2] == period:
                            assignments_for_slot.append(var)
                    
                    if assignments_for_slot:
                        self.model.Add(sum(assignments_for_slot) <= 1)
        
        # Contrainte 3: Une salle ne peut être utilisée que pour un cours à la fois
        for room in self.rooms:
            for day_idx in range(len(DAYS)):
                max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                for period in range(max_period):
                    assignments_for_slot = []
                    for key, var in self.assignments.items():
                        if key[5] == room.id and key[1] == day_idx and key[2] == period:
                            assignments_for_slot.append(var)
                    
                    if assignments_for_slot:
                        self.model.Add(sum(assignments_for_slot) <= 1)
        
        # Contrainte 4: Respecter les disponibilités des enseignants
        for key, var in self.assignments.items():
            class_id, day_idx, period, teacher_id, subject_id, room_id = key
            if not self.teacher_availability.get((teacher_id, day_idx, period), True):
                self.model.Add(var == 0)
        
        # Contrainte 5: Respecter les disponibilités des salles
        for key, var in self.assignments.items():
            class_id, day_idx, period, teacher_id, subject_id, room_id = key
            if not self.room_availability.get((room_id, day_idx, period), True):
                self.model.Add(var == 0)
        
        # Contrainte 6: Respecter le nombre d'heures requis par matière et classe
        for (class_id, subject_id), hours_required in self.requirements.items():
            assignments_for_requirement = []
            for key, var in self.assignments.items():
                if key[0] == class_id and key[4] == subject_id:
                    assignments_for_requirement.append(var)
            
            if assignments_for_requirement:
                self.model.Add(sum(assignments_for_requirement) == hours_required)
        
        # Contrainte 7: Limiter les heures par semaine pour chaque enseignant
        for teacher in self.teachers:
            teacher_assignments = []
            for key, var in self.assignments.items():
                if key[3] == teacher.id:
                    teacher_assignments.append(var)
            
            if teacher_assignments and teacher.max_hours_per_week:
                self.model.Add(sum(teacher_assignments) <= teacher.max_hours_per_week)
        
        # Objectif : Minimiser les trous dans l'emploi du temps des enseignants
        self._add_gap_minimization_objective()
    
    def _add_gap_minimization_objective(self):
        """Ajouter l'objectif de minimisation des trous dans l'emploi du temps."""
        gap_vars = []
        
        for teacher in self.teachers:
            for day_idx in range(len(DAYS)):
                max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                
                # Variables pour détecter le début et la fin de la journée
                first_period = self.model.NewIntVar(0, max_period - 1, f"first_t{teacher.id}_d{day_idx}")
                last_period = self.model.NewIntVar(0, max_period - 1, f"last_t{teacher.id}_d{day_idx}")
                
                # Trouver la première et dernière période de cours
                for period in range(max_period):
                    has_class = self.model.NewBoolVar(f"has_class_t{teacher.id}_d{day_idx}_p{period}")
                    
                    # has_class est vrai si l'enseignant a un cours à cette période
                    period_assignments = []
                    for key, var in self.assignments.items():
                        if key[3] == teacher.id and key[1] == day_idx and key[2] == period:
                            period_assignments.append(var)
                    
                    if period_assignments:
                        self.model.Add(has_class == sum(period_assignments))
                    else:
                        self.model.Add(has_class == 0)
                    
                    # Contraintes pour first_period et last_period
                    self.model.Add(first_period <= period).OnlyEnforceIf(has_class)
                    self.model.Add(last_period >= period).OnlyEnforceIf(has_class)
                
                # Calculer le nombre de trous
                gaps = self.model.NewIntVar(0, max_period, f"gaps_t{teacher.id}_d{day_idx}")
                total_periods = self.model.NewIntVar(0, max_period, f"total_t{teacher.id}_d{day_idx}")
                
                # Compter le nombre total de périodes de cours
                day_assignments = []
                for period in range(max_period):
                    for key, var in self.assignments.items():
                        if key[3] == teacher.id and key[1] == day_idx and key[2] == period:
                            day_assignments.append(var)
                
                if day_assignments:
                    self.model.Add(total_periods == sum(day_assignments))
                else:
                    self.model.Add(total_periods == 0)
                
                # gaps = (last_period - first_period + 1) - total_periods
                span = self.model.NewIntVar(0, max_period, f"span_t{teacher.id}_d{day_idx}")
                self.model.Add(span == last_period - first_period + 1).OnlyEnforceIf(total_periods > 0)
                self.model.Add(span == 0).OnlyEnforceIf(total_periods == 0)
                self.model.Add(gaps == span - total_periods)
                
                gap_vars.append(gaps)
        
        # Minimiser la somme totale des trous
        self.model.Minimize(sum(gap_vars))
    
    def solve(self, time_limit_seconds: Optional[int] = 300) -> Dict[str, Any]:
        """Résoudre le modèle et retourner la solution."""
        logger.info(f"Starting solver with time limit: {time_limit_seconds}s")
        
        # Configurer le solver
        if time_limit_seconds:
            self.solver.parameters.max_time_in_seconds = time_limit_seconds
        
        # Résoudre
        start_time = datetime.now()
        status = self.solver.Solve(self.model)
        solve_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Solver finished with status: {self.solver.StatusName(status)}")
        logger.info(f"Solve time: {solve_time:.2f}s")
        
        # Préparer le résultat
        result = {
            'status': self._get_status_string(status),
            'objective_value': self.solver.ObjectiveValue() if status in [cp_model.OPTIMAL, cp_model.FEASIBLE] else None,
            'solution_time': solve_time,
            'assignments': [],
            'conflicts': [],
            'statistics': {
                'num_branches': self.solver.NumBranches(),
                'num_conflicts': self.solver.NumConflicts(),
                'wall_time': self.solver.WallTime()
            }
        }
        
        # Extraire la solution si trouvée
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            result['assignments'] = self._extract_solution()
            result['conflicts'] = self._check_conflicts(result['assignments'])
        else:
            result['conflicts'] = self._analyze_infeasibility()
        
        return result
    
    def _get_status_string(self, status: int) -> str:
        """Convertir le statut CP-SAT en chaîne."""
        status_map = {
            cp_model.OPTIMAL: 'optimal',
            cp_model.FEASIBLE: 'feasible',
            cp_model.INFEASIBLE: 'infeasible',
            cp_model.MODEL_INVALID: 'invalid',
            cp_model.UNKNOWN: 'unknown'
        }
        return status_map.get(status, 'unknown')
    
    def _extract_solution(self) -> List[Dict[str, Any]]:
        """Extraire les assignations de la solution."""
        assignments = []
        
        for key, var in self.assignments.items():
            if self.solver.Value(var):
                class_id, day_idx, period, teacher_id, subject_id, room_id = key
                
                assignment = {
                    'class_id': class_id,
                    'day': DAYS[day_idx],
                    'period': period,
                    'teacher_id': teacher_id,
                    'subject_id': subject_id,
                    'room_id': room_id
                }
                assignments.append(assignment)
        
        logger.info(f"Extracted {len(assignments)} assignments")
        return assignments
    
    def _check_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Vérifier les conflits potentiels dans la solution."""
        conflicts = []
        
        # Vérifier les conflits d'enseignant (ne devrait pas arriver avec les contraintes)
        teacher_slots = defaultdict(list)
        for assign in assignments:
            key = (assign['teacher_id'], assign['day'], assign['period'])
            teacher_slots[key].append(assign)
        
        for key, assigns in teacher_slots.items():
            if len(assigns) > 1:
                conflicts.append({
                    'type': 'teacher_conflict',
                    'description': f"Teacher {key[0]} assigned to multiple classes at {key[1]} period {key[2]}",
                    'assignments': assigns
                })
        
        # Vérifier les conflits de salle
        room_slots = defaultdict(list)
        for assign in assignments:
            key = (assign['room_id'], assign['day'], assign['period'])
            room_slots[key].append(assign)
        
        for key, assigns in room_slots.items():
            if len(assigns) > 1:
                conflicts.append({
                    'type': 'room_conflict',
                    'description': f"Room {key[0]} assigned to multiple classes at {key[1]} period {key[2]}",
                    'assignments': assigns
                })
        
        return conflicts
    
    def _analyze_infeasibility(self) -> List[Dict[str, Any]]:
        """Analyser pourquoi le problème est infaisable."""
        conflicts = []
        
        # Vérifier si les heures requises dépassent la disponibilité
        for (class_id, subject_id), hours_required in self.requirements.items():
            available_slots = 0
            for teacher in self.teachers:
                if subject_id in self.teacher_subjects.get(teacher.id, []):
                    for day_idx in range(len(DAYS)):
                        max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                        for period in range(max_period):
                            if self.teacher_availability.get((teacher.id, day_idx, period), True):
                                available_slots += 1
            
            if available_slots < hours_required:
                conflicts.append({
                    'type': 'insufficient_availability',
                    'description': f"Class {class_id} needs {hours_required} hours of subject {subject_id} but only {available_slots} slots available",
                    'class_id': class_id,
                    'subject_id': subject_id
                })
        
        return conflicts 