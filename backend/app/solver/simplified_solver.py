"""
Simplified Timetable Solver using Google OR-Tools CP-SAT.

This solver addresses the critical issues found in the original implementation:
- Fixes model field inconsistencies
- Uses correct OR-Tools CP-SAT patterns
- Clear modular structure
- Proper error handling and logging
- Essential constraints only for maintainability
"""

from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from ortools.sat.python import cp_model
import logging
from datetime import datetime, time
from collections import defaultdict

from app.models.teacher import Teacher
from app.models.subject import Subject
from app.models.class_group import ClassGroup
from app.models.room import Room
from app.models.constraint import TeacherAvailability, RoomUnavailability, ClassSubjectRequirement

logger = logging.getLogger(__name__)

# Constants
DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']
PERIODS_PER_DAY = 8
FRIDAY_MAX_PERIOD = 6  # Friday ends at period 6 (1 PM)


class SimplifiedTimetableSolver:
    """Simplified timetable solver with essential functionality."""
    
    def __init__(self, db: Session):
        """Initialize the solver with database session."""
        self.db = db
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # Problem data
        self.teachers = []
        self.subjects = []
        self.classes = []
        self.rooms = []
        
        # Mappings and constraints data
        self.teacher_subjects = {}  # teacher_id -> [subject_ids]
        self.class_requirements = {}  # (class_id, subject_id) -> hours_per_week
        self.teacher_availability = {}  # (teacher_id, day_idx, period) -> bool
        self.room_availability = {}  # (room_id, day_idx, period) -> bool
        
        # Decision variables
        self.assignments = {}  # (class_id, day_idx, period, teacher_id, subject_id, room_id) -> BoolVar
        
        # Validation errors
        self.validation_errors = []
        
        logger.info("SimplifiedTimetableSolver initialized")
    
    def load_data(self) -> bool:
        """
        Load all necessary data from database.
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        logger.info("Loading data from database...")
        
        try:
            # Load teachers
            self.teachers = self.db.query(Teacher).filter(Teacher.is_active == True).all()
            logger.info(f"Loaded {len(self.teachers)} active teachers")
            
            # Load subjects  
            self.subjects = self.db.query(Subject).all()
            logger.info(f"Loaded {len(self.subjects)} subjects")
            
            # Load classes
            self.classes = self.db.query(ClassGroup).filter(ClassGroup.is_active == True).all()
            logger.info(f"Loaded {len(self.classes)} active classes")
            
            # Load rooms
            self.rooms = self.db.query(Room).filter(Room.is_active == True).all()
            logger.info(f"Loaded {len(self.rooms)} active rooms")
            
            # Load teacher-subject relationships
            self._load_teacher_subjects()
            
            # Load class requirements
            self._load_class_requirements()
            
            # Load availabilities
            self._load_teacher_availability()
            self._load_room_availability()
            
            # Validate loaded data
            return self._validate_data()
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.validation_errors.append(f"Database error: {e}")
            return False
    
    def _load_teacher_subjects(self):
        """Load teacher-subject relationships."""
        for teacher in self.teachers:
            self.teacher_subjects[teacher.id] = [subject.id for subject in teacher.subjects]
            logger.debug(f"Teacher {teacher.id} can teach subjects: {self.teacher_subjects[teacher.id]}")
    
    def _load_class_requirements(self):
        """Load class subject requirements."""
        requirements = self.db.query(ClassSubjectRequirement).all()
        for req in requirements:
            key = (req.class_group_id, req.subject_id)
            self.class_requirements[key] = req.hours_per_week
            logger.debug(f"Class {req.class_group_id} needs {req.hours_per_week} hours of subject {req.subject_id}")
        
        logger.info(f"Loaded {len(self.class_requirements)} class requirements")
    
    def _load_teacher_availability(self):
        """Load teacher availability constraints."""
        # Initialize all slots as available
        for teacher in self.teachers:
            for day_idx in range(len(DAYS)):
                max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                for period in range(max_period):
                    self.teacher_availability[(teacher.id, day_idx, period)] = True
        
        # Apply unavailability constraints
        unavailabilities = self.db.query(TeacherAvailability).filter(
            TeacherAvailability.is_available == False
        ).all()
        
        for unavail in unavailabilities:
            day_idx = unavail.day_of_week.value  # Use enum value
            start_period = self._time_to_period(unavail.start_time)
            end_period = self._time_to_period(unavail.end_time)
            
            for period in range(start_period, end_period):
                key = (unavail.teacher_id, day_idx, period)
                self.teacher_availability[key] = False
                logger.debug(f"Teacher {unavail.teacher_id} unavailable on {DAYS[day_idx]} period {period}")
        
        logger.info(f"Applied {len(unavailabilities)} teacher unavailability constraints")
    
    def _load_room_availability(self):
        """Load room availability constraints."""
        # Initialize all slots as available
        for room in self.rooms:
            for day_idx in range(len(DAYS)):
                max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                for period in range(max_period):
                    self.room_availability[(room.id, day_idx, period)] = True
        
        # Apply unavailability constraints
        unavailabilities = self.db.query(RoomUnavailability).all()
        
        for unavail in unavailabilities:
            day_idx = unavail.day_of_week.value  # Use enum value
            start_period = self._time_to_period(unavail.start_time)
            end_period = self._time_to_period(unavail.end_time)
            
            for period in range(start_period, end_period):
                key = (unavail.room_id, day_idx, period)
                self.room_availability[key] = False
                logger.debug(f"Room {unavail.room_id} unavailable on {DAYS[day_idx]} period {period}")
        
        logger.info(f"Applied {len(unavailabilities)} room unavailability constraints")
    
    def _time_to_period(self, time_obj) -> int:
        """
        Convert time to period number.
        
        Args:
            time_obj: Time object or string in HH:MM format
        
        Returns:
            int: Period number (0-7)
        """
        if isinstance(time_obj, str):
            hour, minute = map(int, time_obj.split(':'))
        elif isinstance(time_obj, time):
            hour, minute = time_obj.hour, time_obj.minute
        else:
            logger.warning(f"Unexpected time format: {time_obj}")
            return 0
        
        # School starts at 8:00
        # Period 0: 8:00-8:45, Period 1: 8:50-9:35, etc.
        if hour < 8:
            return 0
        
        period = (hour - 8) * 2
        if minute >= 45:  # Second half of hour
            period += 1
        
        return min(period, PERIODS_PER_DAY - 1)
    
    def _validate_data(self) -> bool:
        """
        Validate loaded data for consistency.
        
        Returns:
            bool: True if data is valid, False otherwise
        """
        is_valid = True
        
        # Check if we have essential data
        if not self.teachers:
            self.validation_errors.append("No active teachers found")
            is_valid = False
        
        if not self.subjects:
            self.validation_errors.append("No subjects found")
            is_valid = False
        
        if not self.classes:
            self.validation_errors.append("No active classes found")
            is_valid = False
        
        if not self.rooms:
            self.validation_errors.append("No active rooms found")
            is_valid = False
        
        if not self.class_requirements:
            self.validation_errors.append("No class requirements found")
            is_valid = False
        
        # Check if teachers can teach required subjects
        for (class_id, subject_id), hours in self.class_requirements.items():
            teachers_for_subject = [
                t_id for t_id, subjects in self.teacher_subjects.items() 
                if subject_id in subjects
            ]
            if not teachers_for_subject:
                self.validation_errors.append(
                    f"No teacher available for subject {subject_id} required by class {class_id}"
                )
                is_valid = False
        
        # Check room capacities
        for class_group in self.classes:
            student_count = getattr(class_group, 'student_count', None) or getattr(class_group, 'effectif', 0)
            suitable_rooms = [
                room for room in self.rooms 
                if (getattr(room, 'capacity', None) or getattr(room, 'capacite', 0)) >= student_count
            ]
            if not suitable_rooms:
                self.validation_errors.append(
                    f"No room with sufficient capacity for class {class_group.id} ({student_count} students)"
                )
                is_valid = False
        
        if is_valid:
            logger.info("Data validation passed")
        else:
            logger.error(f"Data validation failed: {self.validation_errors}")
        
        return is_valid
    
    def _create_variables(self):
        """Create decision variables for the CP-SAT model."""
        logger.info("Creating decision variables...")
        
        variable_count = 0
        
        for class_group in self.classes:
            for day_idx in range(len(DAYS)):
                max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                
                for period in range(max_period):
                    for teacher in self.teachers:
                        # Check if teacher is available
                        if not self.teacher_availability.get((teacher.id, day_idx, period), True):
                            continue
                        
                        for subject in self.subjects:
                            # Check if teacher can teach this subject
                            if subject.id not in self.teacher_subjects.get(teacher.id, []):
                                continue
                            
                            # Check if this class needs this subject
                            if (class_group.id, subject.id) not in self.class_requirements:
                                continue
                            
                            for room in self.rooms:
                                # Check room availability
                                if not self.room_availability.get((room.id, day_idx, period), True):
                                    continue
                                
                                # Check room capacity
                                student_count = getattr(class_group, 'student_count', None) or getattr(class_group, 'effectif', 0)
                                room_capacity = getattr(room, 'capacity', None) or getattr(room, 'capacite', 0)
                                
                                if room_capacity < student_count:
                                    continue
                                
                                # Create variable
                                var_name = f"c{class_group.id}_d{day_idx}_p{period}_t{teacher.id}_s{subject.id}_r{room.id}"
                                var = self.model.NewBoolVar(var_name)
                                
                                key = (class_group.id, day_idx, period, teacher.id, subject.id, room.id)
                                self.assignments[key] = var
                                variable_count += 1
        
        logger.info(f"Created {variable_count} decision variables")
        
        if variable_count == 0:
            logger.error("No valid variables created - check data consistency")
            return False
        
        return True
    
    def _add_constraints(self):
        """Add all constraints to the model."""
        logger.info("Adding constraints...")
        
        # Constraint 1: Each class can have at most one lesson per time slot
        self._add_class_conflicts_constraints()
        
        # Constraint 2: Each teacher can teach at most one class per time slot
        self._add_teacher_conflicts_constraints()
        
        # Constraint 3: Each room can host at most one class per time slot
        self._add_room_conflicts_constraints()
        
        # Constraint 4: Satisfy required hours per subject per class
        self._add_hours_requirements_constraints()
        
        # Constraint 5: Respect teacher max hours per week
        self._add_teacher_max_hours_constraints()
        
        logger.info("All constraints added successfully")
    
    def _add_class_conflicts_constraints(self):
        """Ensure each class has at most one lesson per time slot."""
        constraint_count = 0
        
        for class_group in self.classes:
            for day_idx in range(len(DAYS)):
                max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                
                for period in range(max_period):
                    # Find all assignments for this class at this time slot
                    slot_assignments = []
                    for key, var in self.assignments.items():
                        if key[0] == class_group.id and key[1] == day_idx and key[2] == period:
                            slot_assignments.append(var)
                    
                    if slot_assignments:
                        self.model.Add(sum(slot_assignments) <= 1)
                        constraint_count += 1
        
        logger.debug(f"Added {constraint_count} class conflict constraints")
    
    def _add_teacher_conflicts_constraints(self):
        """Ensure each teacher teaches at most one class per time slot."""
        constraint_count = 0
        
        for teacher in self.teachers:
            for day_idx in range(len(DAYS)):
                max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                
                for period in range(max_period):
                    # Find all assignments for this teacher at this time slot
                    slot_assignments = []
                    for key, var in self.assignments.items():
                        if key[3] == teacher.id and key[1] == day_idx and key[2] == period:
                            slot_assignments.append(var)
                    
                    if slot_assignments:
                        self.model.Add(sum(slot_assignments) <= 1)
                        constraint_count += 1
        
        logger.debug(f"Added {constraint_count} teacher conflict constraints")
    
    def _add_room_conflicts_constraints(self):
        """Ensure each room hosts at most one class per time slot."""
        constraint_count = 0
        
        for room in self.rooms:
            for day_idx in range(len(DAYS)):
                max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                
                for period in range(max_period):
                    # Find all assignments for this room at this time slot
                    slot_assignments = []
                    for key, var in self.assignments.items():
                        if key[5] == room.id and key[1] == day_idx and key[2] == period:
                            slot_assignments.append(var)
                    
                    if slot_assignments:
                        self.model.Add(sum(slot_assignments) <= 1)
                        constraint_count += 1
        
        logger.debug(f"Added {constraint_count} room conflict constraints")
    
    def _add_hours_requirements_constraints(self):
        """Ensure required hours per subject per class are satisfied."""
        constraint_count = 0
        
        for (class_id, subject_id), required_hours in self.class_requirements.items():
            # Find all assignments for this class-subject combination
            subject_assignments = []
            for key, var in self.assignments.items():
                if key[0] == class_id and key[4] == subject_id:
                    subject_assignments.append(var)
            
            if subject_assignments:
                self.model.Add(sum(subject_assignments) == required_hours)
                constraint_count += 1
                logger.debug(f"Class {class_id} must have exactly {required_hours} hours of subject {subject_id}")
        
        logger.debug(f"Added {constraint_count} hours requirement constraints")
    
    def _add_teacher_max_hours_constraints(self):
        """Ensure teachers don't exceed their maximum hours per week."""
        constraint_count = 0
        
        for teacher in self.teachers:
            if not teacher.max_hours_per_week:
                continue
            
            # Find all assignments for this teacher
            teacher_assignments = []
            for key, var in self.assignments.items():
                if key[3] == teacher.id:
                    teacher_assignments.append(var)
            
            if teacher_assignments:
                self.model.Add(sum(teacher_assignments) <= teacher.max_hours_per_week)
                constraint_count += 1
                logger.debug(f"Teacher {teacher.id} limited to {teacher.max_hours_per_week} hours per week")
        
        logger.debug(f"Added {constraint_count} teacher max hours constraints")
    
    def solve(self, time_limit_seconds: Optional[int] = 300) -> Dict[str, Any]:
        """
        Solve the timetable problem.
        
        Args:
            time_limit_seconds: Maximum time to spend solving (default: 5 minutes)
        
        Returns:
            Dict with solution status, assignments, and metadata
        """
        logger.info(f"Starting timetable solving with {time_limit_seconds}s time limit...")
        
        # Load data
        if not self.load_data():
            return {
                'status': 'invalid_data',
                'assignments': [],
                'solution_time': 0,
                'conflicts': [],
                'errors': self.validation_errors
            }
        
        # Create variables
        if not self._create_variables():
            return {
                'status': 'no_variables',
                'assignments': [],
                'solution_time': 0,
                'conflicts': [],
                'errors': ['No valid assignment variables could be created']
            }
        
        # Add constraints
        try:
            self._add_constraints()
        except Exception as e:
            logger.error(f"Error adding constraints: {e}")
            return {
                'status': 'constraint_error',
                'assignments': [],
                'solution_time': 0,
                'conflicts': [],
                'errors': [f'Error adding constraints: {e}']
            }
        
        # Configure solver
        if time_limit_seconds:
            self.solver.parameters.max_time_in_seconds = time_limit_seconds
        
        # Solve
        start_time = datetime.now()
        status = self.solver.Solve(self.model)
        solve_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Solver finished with status: {self.solver.StatusName(status)} in {solve_time:.2f}s")
        
        # Prepare result
        result = {
            'status': self._get_status_string(status),
            'solution_time': solve_time,
            'assignments': [],
            'conflicts': [],
            'statistics': {
                'num_branches': self.solver.NumBranches(),
                'num_conflicts': self.solver.NumConflicts(),
                'wall_time': self.solver.WallTime(),
                'num_variables': len(self.assignments)
            }
        }
        
        # Extract solution if found
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            result['assignments'] = self._extract_solution()
            # Only get objective value if we have an objective function (we don't in this case)
            try:
                result['objective_value'] = self.solver.ObjectiveValue()
            except:
                result['objective_value'] = None
            result['conflicts'] = self._validate_solution(result['assignments'])
            logger.info(f"Solution found with {len(result['assignments'])} assignments")
        else:
            result['conflicts'] = self._analyze_infeasibility()
            logger.warning(f"No solution found: {result['status']}")
        
        return result
    
    def _get_status_string(self, status: int) -> str:
        """Convert CP-SAT status to string."""
        status_map = {
            cp_model.OPTIMAL: 'optimal',
            cp_model.FEASIBLE: 'feasible', 
            cp_model.INFEASIBLE: 'infeasible',
            cp_model.MODEL_INVALID: 'invalid',
            cp_model.UNKNOWN: 'unknown'
        }
        return status_map.get(status, 'unknown')
    
    def _extract_solution(self) -> List[Dict[str, Any]]:
        """Extract assignments from the solution."""
        assignments = []
        
        for key, var in self.assignments.items():
            if self.solver.Value(var):
                class_id, day_idx, period, teacher_id, subject_id, room_id = key
                
                assignment = {
                    'class_id': class_id,
                    'day': DAYS[day_idx],
                    'day_index': day_idx,
                    'period': period,
                    'teacher_id': teacher_id,
                    'subject_id': subject_id,
                    'room_id': room_id,
                    'start_time': self._period_to_time(period),
                    'end_time': self._period_to_time(period + 1)
                }
                assignments.append(assignment)
        
        return sorted(assignments, key=lambda x: (x['day_index'], x['period'], x['class_id']))
    
    def _period_to_time(self, period: int) -> str:
        """Convert period number to time string."""
        start_hour = 8 + (period // 2)
        start_minute = 0 if period % 2 == 0 else 50
        return f"{start_hour:02d}:{start_minute:02d}"
    
    def _validate_solution(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate the solution for potential conflicts."""
        conflicts = []
        
        # Group assignments by time slot
        slots = defaultdict(list)
        for assignment in assignments:
            key = (assignment['day'], assignment['period'])
            slots[key].append(assignment)
        
        # Check for conflicts in each slot
        for (day, period), slot_assignments in slots.items():
            # Check teacher conflicts
            teachers_in_slot = defaultdict(list)
            for assignment in slot_assignments:
                teachers_in_slot[assignment['teacher_id']].append(assignment)
            
            for teacher_id, teacher_assignments in teachers_in_slot.items():
                if len(teacher_assignments) > 1:
                    conflicts.append({
                        'type': 'teacher_conflict',
                        'description': f"Teacher {teacher_id} assigned to multiple classes at {day} period {period}",
                        'assignments': teacher_assignments
                    })
            
            # Check room conflicts
            rooms_in_slot = defaultdict(list)
            for assignment in slot_assignments:
                rooms_in_slot[assignment['room_id']].append(assignment)
            
            for room_id, room_assignments in rooms_in_slot.items():
                if len(room_assignments) > 1:
                    conflicts.append({
                        'type': 'room_conflict',
                        'description': f"Room {room_id} assigned to multiple classes at {day} period {period}",
                        'assignments': room_assignments
                    })
        
        return conflicts
    
    def _analyze_infeasibility(self) -> List[Dict[str, Any]]:
        """Analyze why the problem is infeasible."""
        issues = []
        
        # Check if requirements can be satisfied
        for (class_id, subject_id), required_hours in self.class_requirements.items():
            # Count available teacher-hours for this subject
            available_hours = 0
            teachers_for_subject = [
                t_id for t_id, subjects in self.teacher_subjects.items() 
                if subject_id in subjects
            ]
            
            for teacher_id in teachers_for_subject:
                # Count available time slots for this teacher
                for day_idx in range(len(DAYS)):
                    max_period = FRIDAY_MAX_PERIOD if day_idx == 5 else PERIODS_PER_DAY
                    for period in range(max_period):
                        if self.teacher_availability.get((teacher_id, day_idx, period), True):
                            available_hours += 1
            
            if available_hours < required_hours:
                issues.append({
                    'type': 'insufficient_teacher_hours',
                    'description': f"Class {class_id} needs {required_hours} hours of subject {subject_id}, but only {available_hours} teacher-hours available",
                    'class_id': class_id,
                    'subject_id': subject_id,
                    'required': required_hours,
                    'available': available_hours
                })
        
        return issues 