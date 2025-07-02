"""
Tests for SimplifiedTimetableSolver.

This module contains comprehensive tests for the timetable solver including:
- Initialization testing
- Data loading validation
- Simple scheduling scenarios
- Constraint validation
- Infeasible problem handling
- Performance testing
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, date, time as dt_time
from typing import Dict, List, Any

from app.solver.simplified_solver import SimplifiedTimetableSolver, DAYS, PERIODS_PER_DAY, FRIDAY_MAX_PERIOD
from app.models.teacher import Teacher
from app.models.subject import Subject, SubjectType
from app.models.class_group import ClassGroup, ClassType
from app.models.room import Room, RoomType
from app.models.constraint import ClassSubjectRequirement, TeacherAvailability, RoomUnavailability, DayOfWeek


class TestSimplifiedSolverInitialization:
    """Test suite for solver initialization."""
    
    def test_solver_initialization(self, db_session):
        """Test that solver initializes correctly with database session."""
        # Create solver
        solver = SimplifiedTimetableSolver(db_session)
        
        # Verify initialization
        assert solver.db == db_session
        assert solver.model is not None
        assert solver.solver is not None
        
        # Verify empty collections
        assert solver.teachers == []
        assert solver.subjects == []
        assert solver.classes == []
        assert solver.rooms == []
        
        # Verify empty mappings
        assert solver.teacher_subjects == {}
        assert solver.class_requirements == {}
        assert solver.teacher_availability == {}
        assert solver.room_availability == {}
        assert solver.assignments == {}
        
        # Verify empty validation errors
        assert solver.validation_errors == []
    
    def test_solver_initialization_with_invalid_db(self):
        """Test solver initialization with invalid database session."""
        # Should not raise exception during initialization
        solver = SimplifiedTimetableSolver(None)
        assert solver.db is None
        
        # But should fail when trying to load data
        result = solver.load_data()
        assert result is False
        assert len(solver.validation_errors) > 0


class TestDataLoading:
    """Test suite for data loading functionality."""
    
    def test_load_data_success(self, db_session, test_data):
        """Test successful data loading from database."""
        # Create class requirements
        req1 = ClassSubjectRequirement(
            class_id=test_data['class_groups'][0].id,
            subject_id=test_data['subjects'][0].id,
            hours_per_week=4
        )
        req2 = ClassSubjectRequirement(
            class_id=test_data['class_groups'][0].id,
            subject_id=test_data['subjects'][1].id,
            hours_per_week=3
        )
        db_session.add_all([req1, req2])
        db_session.commit()
        
        # Create and test solver
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.load_data()
        
        # Verify successful loading
        assert result is True
        assert len(solver.teachers) > 0
        assert len(solver.subjects) > 0
        assert len(solver.classes) > 0
        assert len(solver.rooms) > 0
        assert len(solver.class_requirements) > 0
        assert len(solver.validation_errors) == 0
    
    def test_load_data_with_empty_database(self, empty_db_session):
        """Test data loading with empty database."""
        solver = SimplifiedTimetableSolver(empty_db_session)
        result = solver.load_data()
        
        # Should fail due to missing data
        assert result is False
        assert len(solver.validation_errors) > 0
        
        # Check specific error messages
        error_messages = " ".join(solver.validation_errors)
        assert "No active teachers found" in error_messages
        assert "No subjects found" in error_messages
        assert "No active classes found" in error_messages
        assert "No active rooms found" in error_messages
    
    def test_load_data_with_missing_requirements(self, db_session, test_data):
        """Test data loading when class requirements are missing."""
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.load_data()
        
        # Should fail due to missing class requirements
        assert result is False
        assert "No class requirements found" in solver.validation_errors
    
    def test_load_data_with_incompatible_teacher_subjects(self, db_session, test_data):
        """Test data loading when no teacher can teach required subjects."""
        # Create requirement for subject that no teacher can teach
        unknown_subject = Subject(
            code="UNKNOWN",
            name_he="לא ידוע",
            name_fr="Inconnu",
            subject_type=SubjectType.ACADEMIC,
            is_active=True
        )
        db_session.add(unknown_subject)
        db_session.commit()
        
        req = ClassSubjectRequirement(
            class_id=test_data['class_groups'][0].id,
            subject_id=unknown_subject.id,
            hours_per_week=2
        )
        db_session.add(req)
        db_session.commit()
        
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.load_data()
        
        # Should fail due to missing teacher for subject
        assert result is False
        assert any("No teacher available for subject" in error for error in solver.validation_errors)


class TestSimpleScheduling:
    """Test suite for simple scheduling scenarios."""
    
    def test_simple_schedule_minimal_case(self, db_session):
        """Test scheduling with 1 class, 2 subjects, 2 teachers - minimal viable case."""
        # Create minimal test data
        
        # 1 Subject: Math
        subject_math = Subject(
            code="MATH",
            name_he="מתמטיקה",
            name_fr="Mathématiques",
            subject_type=SubjectType.ACADEMIC,
            is_active=True
        )
        
        # 1 Subject: Science
        subject_science = Subject(
            code="SCI",
            name_he="מדעים",
            name_fr="Sciences",
            subject_type=SubjectType.ACADEMIC,
            is_active=True
        )
        
        db_session.add_all([subject_math, subject_science])
        db_session.commit()
        
        # 2 Teachers
        teacher_math = Teacher(
            code="T001",
            first_name="יוסי",
            last_name="מתמטיקאי",
            email="math@school.edu",
            max_hours_per_week=20,
            is_active=True
        )
        teacher_science = Teacher(
            code="T002",
            first_name="מרים",
            last_name="מדענית",
            email="science@school.edu",
            max_hours_per_week=20,
            is_active=True
        )
        
        db_session.add_all([teacher_math, teacher_science])
        db_session.commit()
        
        # Assign subjects to teachers
        teacher_math.subjects = [subject_math]
        teacher_science.subjects = [subject_science]
        db_session.commit()
        
        # 1 Class
        class_9a = ClassGroup(
            code="9A",
            name="כיתה ט'א",
            grade_level="9",
            student_count=25,
            class_type=ClassType.REGULAR,
            is_active=True
        )
        db_session.add(class_9a)
        db_session.commit()
        
        # 1 Room
        room = Room(
            code="A101",
            name="כיתה א101",
            capacity=30,
            room_type=RoomType.REGULAR_CLASSROOM,
            is_active=True
        )
        db_session.add(room)
        db_session.commit()
        
        # Class requirements - minimal hours
        req_math = ClassSubjectRequirement(
            class_id=class_9a.id,
            subject_id=subject_math.id,
            hours_per_week=2
        )
        req_science = ClassSubjectRequirement(
            class_id=class_9a.id,
            subject_id=subject_science.id,
            hours_per_week=2
        )
        db_session.add_all([req_math, req_science])
        db_session.commit()
        
        # Test solver
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=30)
        
        # Verify solution
        assert result['status'] in ['optimal', 'feasible']
        assert len(result['assignments']) == 4  # 2 subjects × 2 hours each
        assert result['solution_time'] < 30
        assert len(result['conflicts']) == 0
        
        # Verify all assignments have required fields
        for assignment in result['assignments']:
            assert 'class_id' in assignment
            assert 'day' in assignment
            assert 'period' in assignment
            assert 'teacher_id' in assignment
            assert 'subject_id' in assignment
            assert 'room_id' in assignment
            assert 'start_time' in assignment
            assert 'end_time' in assignment
    
    def test_simple_schedule_with_larger_case(self, db_session, test_data):
        """Test scheduling with multiple classes and subjects."""
        # Add class requirements for test data
        requirements = []
        for class_group in test_data['class_groups'][:2]:  # Use first 2 classes
            for subject in test_data['subjects'][:2]:  # Use first 2 subjects
                req = ClassSubjectRequirement(
                    class_id=class_group.id,
                    subject_id=subject.id,
                    hours_per_week=2
                )
                requirements.append(req)
        
        db_session.add_all(requirements)
        db_session.commit()
        
        # Test solver
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=60)
        
        # Verify solution
        assert result['status'] in ['optimal', 'feasible']
        assert len(result['assignments']) > 0
        assert result['solution_time'] < 60
        
        # Verify no scheduling conflicts
        assert len(result['conflicts']) == 0


class TestConstraintRespect:
    """Test suite for constraint validation."""
    
    def test_teacher_availability_constraints(self, db_session, test_data):
        """Test that teacher availability constraints are respected."""
        # Add class requirement
        req = ClassSubjectRequirement(
            class_id=test_data['class_groups'][0].id,
            subject_id=test_data['subjects'][0].id,
            hours_per_week=2
        )
        db_session.add(req)
        
        # Make teacher unavailable on Sunday, period 0
        unavail = TeacherAvailability(
            teacher_id=test_data['teachers'][0].id,
            day_of_week=DayOfWeek.SUNDAY,
            start_time=dt_time(8, 0),
            end_time=dt_time(8, 45),
            is_available=False
        )
        db_session.add(unavail)
        db_session.commit()
        
        # Test solver
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=30)
        
        if result['status'] in ['optimal', 'feasible']:
            # Verify teacher is not scheduled during unavailable time
            for assignment in result['assignments']:
                if assignment['teacher_id'] == test_data['teachers'][0].id:
                    assert not (assignment['day'] == 'sunday' and assignment['period'] == 0)
    
    def test_room_capacity_constraints(self, db_session, test_data):
        """Test that room capacity constraints are respected."""
        # Create a small room
        small_room = Room(
            code="SMALL",
            name="חדר קטן",
            capacity=5,  # Smaller than class size
            room_type=RoomType.REGULAR_CLASSROOM,
            is_active=True
        )
        db_session.add(small_room)
        
        # Add class requirement
        req = ClassSubjectRequirement(
            class_id=test_data['class_groups'][0].id,  # 25 students
            subject_id=test_data['subjects'][0].id,
            hours_per_week=2
        )
        db_session.add(req)
        db_session.commit()
        
        # Test solver
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=30)
        
        if result['status'] in ['optimal', 'feasible']:
            # Verify large class is not assigned to small room
            for assignment in result['assignments']:
                if assignment['class_id'] == test_data['class_groups'][0].id:
                    assert assignment['room_id'] != small_room.id
    
    def test_teacher_subject_constraints(self, db_session, test_data):
        """Test that teachers only teach subjects they're qualified for."""
        # Add class requirement
        req = ClassSubjectRequirement(
           class_id=test_data['class_groups'][0].id,
            subject_id=test_data['subjects'][0].id,  # Math
            hours_per_week=2
        )
        db_session.add(req)
        db_session.commit()
        
        # Test solver
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=30)
        
        if result['status'] in ['optimal', 'feasible']:
            # Verify teachers only teach their subjects
            for assignment in result['assignments']:
                teacher_id = assignment['teacher_id']
                subject_id = assignment['subject_id']
                
                # Find teacher
                teacher = next(t for t in test_data['teachers'] if t.id == teacher_id)
                teacher_subject_ids = [s.id for s in teacher.subjects]
                
                assert subject_id in teacher_subject_ids
    
    def test_no_teacher_conflicts(self, db_session, test_data):
        """Test that teachers are not double-booked."""
        # Add multiple class requirements to potentially create conflicts
        requirements = []
        for class_group in test_data['class_groups']:
            for subject in test_data['subjects'][:2]:
                req = ClassSubjectRequirement(
                    class_id=class_group.id,
                    subject_id=subject.id,
                    hours_per_week=1
                )
                requirements.append(req)
        
        db_session.add_all(requirements)
        db_session.commit()
        
        # Test solver
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=60)
        
        if result['status'] in ['optimal', 'feasible']:
            # Check for teacher conflicts
            time_slots = {}
            for assignment in result['assignments']:
                slot_key = (assignment['day'], assignment['period'])
                if slot_key not in time_slots:
                    time_slots[slot_key] = []
                time_slots[slot_key].append(assignment)
            
            # Verify no teacher conflicts
            for slot_assignments in time_slots.values():
                teachers_in_slot = [a['teacher_id'] for a in slot_assignments]
                assert len(teachers_in_slot) == len(set(teachers_in_slot)), "Teacher conflict detected"


class TestInfeasibleProblems:
    """Test suite for infeasible problem handling."""
    
    def test_infeasible_problem_impossible_hours(self, db_session, test_data):
        """Test with impossible hour requirements."""
        # Create requirement that requires more hours than available in a week
        req = ClassSubjectRequirement(
            class_id=test_data['class_groups'][0].id,
            subject_id=test_data['subjects'][0].id,
            hours_per_week=20 # Impossible - more than total periods in a week
        )
        db_session.add(req)
        db_session.commit()
        
        # Test solver
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=10)
        
        # Should be infeasible
        assert result['status'] == 'infeasible'
        assert len(result['assignments']) == 0
        assert len(result['conflicts']) > 0
        
        # Should provide analysis of infeasibility
        assert any('insufficient_teacher_hours' in str(conflict) for conflict in result['conflicts'])
    
    def test_infeasible_problem_no_qualified_teachers(self, db_session, test_data):
        """Test with subject that no teacher can teach."""
        # Create subject with no qualified teachers
        unknown_subject = Subject(
            code="UNKNOWN",
            name_he="לא ידוע",
            name_fr="Inconnu",
            subject_type=SubjectType.ACADEMIC,
            is_active=True
        )
        db_session.add(unknown_subject)
        db_session.commit()
        
        req = ClassSubjectRequirement(
            class_id=test_data['class_groups'][0].id,
            subject_id=unknown_subject.id,
            hours_per_week=2
        )
        db_session.add(req)
        db_session.commit()
        
        # Test solver
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=10)
        
        # Should fail at data loading stage
        assert result['status'] == 'invalid_data'
        assert len(result['errors']) > 0
        assert any('No teacher available for subject' in error for error in result['errors'])
    
    def test_infeasible_problem_insufficient_rooms(self, db_session, test_data):
        """Test with insufficient room capacity."""
        # Remove all rooms except one small room
        for room in test_data['rooms']:
            room.is_active = False
        
        small_room = Room(
            code="TINY",
            name="חדר זעיר",
            capacity=1,  # Too small for any class
            room_type=RoomType.REGULAR_CLASSROOM,
            is_active=True
        )
        db_session.add(small_room)
        
        req = ClassSubjectRequirement(
           class_id=test_data['class_groups'][0].id,  # 25 students
            subject_id=test_data['subjects'][0].id,
            hours_per_week=2
        )
        db_session.add(req)
        db_session.commit()
        
        # Test solver
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=10)
        
        # Should fail at data validation stage
        assert result['status'] == 'invalid_data'
        assert any('No room with sufficient capacity' in error for error in result['errors'])


class TestPerformance:
    """Test suite for performance requirements."""
    
    def test_performance_simple_case(self, db_session, test_data):
        """Test that simple cases solve quickly (< 30 seconds)."""
        # Add reasonable requirements
        requirements = []
        for class_group in test_data['class_groups'][:2]:  # Limit to 2 classes
            for subject in test_data['subjects'][:2]:  # Limit to 2 subjects
                req = ClassSubjectRequirement(
                    class_id=class_group.id,
                    subject_id=subject.id,
                    hours_per_week=2
                )
                requirements.append(req)
        
        db_session.add_all(requirements)
        db_session.commit()
        
        # Measure performance
        start_time = time.time()
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=30)
        elapsed_time = time.time() - start_time
        
        # Performance assertions
        assert elapsed_time < 30.0, f"Solver took {elapsed_time:.2f}s, expected < 30s"
        assert result['solution_time'] < 30.0
        
        # Should find a solution quickly
        if result['status'] in ['optimal', 'feasible']:
            assert len(result['assignments']) > 0
    
    def test_performance_with_time_limit(self, db_session, test_data):
        """Test that solver respects time limits."""
        # Add complex requirements
        requirements = []
        for class_group in test_data['class_groups']:
            for subject in test_data['subjects']:
                req = ClassSubjectRequirement(
                    class_id=class_group.id,
                    subject_id=subject.id,
                    hours_per_week=3
                )
                requirements.append(req)
        
        db_session.add_all(requirements)
        db_session.commit()
        
        # Test with short time limit
        start_time = time.time()
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=5)
        elapsed_time = time.time() - start_time
        
        # Should respect time limit (with some tolerance for overhead)
        assert elapsed_time < 10.0, f"Solver took {elapsed_time:.2f}s, expected < 10s with 5s limit"
        
        # Result should indicate time limit if no solution found
        if result['status'] == 'unknown':
            assert result['solution_time'] <= 5.5  # Small tolerance for setup time
    
    def test_performance_statistics(self, db_session, test_data):
        """Test that solver provides performance statistics."""
        # Add minimal requirements
        req = ClassSubjectRequirement(
            class_id=test_data['class_groups'][0].id,
            subject_id=test_data['subjects'][0].id,
            hours_per_week=1
        )
        db_session.add(req)
        db_session.commit()
        
        # Test solver
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=30)
        
        # Verify statistics are provided
        assert 'statistics' in result
        stats = result['statistics']
        
        assert 'num_branches' in stats
        assert 'num_conflicts' in stats
        assert 'wall_time' in stats
        assert 'num_variables' in stats
        
        # Verify statistics are reasonable
        assert isinstance(stats['num_branches'], int)
        assert isinstance(stats['num_conflicts'], int)
        assert isinstance(stats['wall_time'], float)
        assert isinstance(stats['num_variables'], int)
        assert stats['num_variables'] > 0


class TestEdgeCases:
    """Test suite for edge cases and error handling."""
    
    def test_solver_with_database_error(self, db_session):
        """Test solver behavior when database errors occur."""
        # Mock database session to raise exception
        with patch.object(db_session, 'query', side_effect=Exception("Database connection lost")):
            solver = SimplifiedTimetableSolver(db_session)
            result = solver.solve(time_limit_seconds=10)
            
            # Should handle error gracefully
            assert result['status'] == 'invalid_data'
            assert len(result['errors']) > 0
            assert 'Database error' in str(result['errors'])
    
    def test_solver_time_conversion(self, db_session):
        """Test time conversion utilities."""
        solver = SimplifiedTimetableSolver(db_session)
        
        # Test _time_to_period method
        assert solver._time_to_period("08:00") == 0
        assert solver._time_to_period("08:45") == 1
        assert solver._time_to_period("09:00") == 2
        assert solver._time_to_period("12:00") == 7
        
        # Test with time objects
        assert solver._time_to_period(dt_time(8, 0)) == 0
        assert solver._time_to_period(dt_time(8, 45)) == 1
        
        # Test _period_to_time method
        assert solver._period_to_time(0) == "08:00"
        assert solver._period_to_time(1) == "08:50"
        assert solver._period_to_time(2) == "09:00"
    
    def test_friday_short_day_handling(self, db_session, test_data):
        """Test that Friday ends at period 6 (1 PM)."""
        # Add requirement
        req = ClassSubjectRequirement(
            class_id=test_data['class_groups'][0].id,
            subject_id=test_data['subjects'][0].id,
            hours_per_week=1
        )
        db_session.add(req)
        db_session.commit()
        
        # Test solver
        solver = SimplifiedTimetableSolver(db_session)
        result = solver.solve(time_limit_seconds=30)
        
        if result['status'] in ['optimal', 'feasible']:
            # Verify no assignments on Friday after period 6
            for assignment in result['assignments']:
                if assignment['day'] == 'friday':
                    assert assignment['period'] < FRIDAY_MAX_PERIOD 