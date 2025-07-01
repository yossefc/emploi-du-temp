"""
Unit tests for TeacherRepository.
"""
import pytest
from datetime import date

from app.repositories.teacher_repository import TeacherRepository
from app.models.teacher import Teacher
from app.schemas.teacher import TeacherCreate


class TestTeacherRepository:
    """Test suite for TeacherRepository."""

    def test_create_teacher(self, db_session, sample_teacher_data):
        """Test creating a teacher in the database."""
        # Arrange
        repository = TeacherRepository(db_session)
        teacher_data = TeacherCreate(**sample_teacher_data)
        
        # Act
        created_teacher = repository.create(teacher_data.dict())
        
        # Assert
        assert created_teacher.id is not None
        assert created_teacher.code == sample_teacher_data["code"]
        assert created_teacher.email == sample_teacher_data["email"]
        assert created_teacher.first_name == sample_teacher_data["first_name"]

    def test_get_by_id(self, db_session, sample_teacher_data):
        """Test retrieving teacher by ID."""
        # Arrange
        repository = TeacherRepository(db_session)
        teacher_data = TeacherCreate(**sample_teacher_data)
        created_teacher = repository.create(teacher_data.dict())
        
        # Act
        retrieved_teacher = repository.get_by_id(created_teacher.id)
        
        # Assert
        assert retrieved_teacher is not None
        assert retrieved_teacher.id == created_teacher.id
        assert retrieved_teacher.code == sample_teacher_data["code"]

    def test_get_by_code(self, db_session, sample_teacher_data):
        """Test retrieving teacher by code."""
        # Arrange
        repository = TeacherRepository(db_session)
        teacher_data = TeacherCreate(**sample_teacher_data)
        created_teacher = repository.create(teacher_data.dict())
        
        # Act
        retrieved_teacher = repository.get_by_code(sample_teacher_data["code"])
        
        # Assert
        assert retrieved_teacher is not None
        assert retrieved_teacher.code == sample_teacher_data["code"]
        assert retrieved_teacher.id == created_teacher.id

    def test_get_active_teachers(self, db_session, sample_teacher_data):
        """Test retrieving only active teachers."""
        # Arrange
        repository = TeacherRepository(db_session)
        
        # Create active teacher
        active_data = sample_teacher_data.copy()
        active_data["is_active"] = True
        active_teacher = repository.create(active_data)
        
        # Create inactive teacher
        inactive_data = sample_teacher_data.copy()
        inactive_data["code"] = "T002"
        inactive_data["email"] = "jane@school.edu"
        inactive_data["is_active"] = False
        repository.create(inactive_data)
        
        # Act
        active_teachers = repository.get_active_teachers()
        
        # Assert
        assert len(active_teachers) == 1
        assert active_teachers[0].is_active is True
        assert active_teachers[0].code == "T001"

    def test_search_teachers(self, db_session, sample_teacher_data):
        """Test searching teachers by query."""
        # Arrange
        repository = TeacherRepository(db_session)
        teacher_data = TeacherCreate(**sample_teacher_data)
        repository.create(teacher_data.dict())
        
        # Act
        results = repository.search_teachers("John")
        
        # Assert
        assert len(results) == 1
        assert results[0].first_name == "John" 