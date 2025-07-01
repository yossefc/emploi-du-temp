"""
Simple tests for TeacherRepository.
"""
import pytest

from app.repositories.teacher_repository import TeacherRepository
from app.models.teacher import Teacher


class TestTeacherRepositorySimple:
    """Test suite for TeacherRepository."""

    def test_create_teacher(self, db_session, sample_teacher_data):
        """Test creating a teacher in the database."""
        # Arrange
        repository = TeacherRepository(db_session)
        
        # Act
        created_teacher = repository.create(sample_teacher_data)
        
        # Assert
        assert created_teacher.id is not None
        assert created_teacher.code == sample_teacher_data["code"]
        assert created_teacher.email == sample_teacher_data["email"]
        assert created_teacher.first_name == sample_teacher_data["first_name"]

    def test_get_by_id(self, db_session, sample_teacher_data):
        """Test retrieving teacher by ID."""
        # Arrange
        repository = TeacherRepository(db_session)
        created_teacher = repository.create(sample_teacher_data)
        
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
        created_teacher = repository.create(sample_teacher_data)
        
        # Act
        retrieved_teacher = repository.get_by_code(sample_teacher_data["code"])
        
        # Assert
        assert retrieved_teacher is not None
        assert retrieved_teacher.code == sample_teacher_data["code"]
        assert retrieved_teacher.id == created_teacher.id 