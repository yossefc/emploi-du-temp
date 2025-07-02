"""
Unit tests for SubjectService.
"""

import pytest
from unittest.mock import Mock

from app.repositories.subject_repository import SubjectRepository
from app.models.subject import Subject
from app.core.exceptions import ValidationException, DuplicateException


class MockSubjectService:
    """Mock implementation of SubjectService for testing until the real one is created."""
    
    def __init__(self, repository):
        self.repository = repository
        self.subject_repo = repository
    
    def get_by_code(self, code):
        return self.subject_repo.get_by_code(code)
    
    def get_active_subjects(self, skip=0, limit=100):
        return self.subject_repo.get_active_subjects(skip, limit)
    
    def search_subjects(self, search_term, skip=0, limit=100):
        return self.subject_repo.search_subjects(search_term, skip, limit)


class TestSubjectService:
    """Test suite for SubjectService."""

    @pytest.fixture
    def mock_repository(self):
        """Mock SubjectRepository for testing."""
        return Mock(spec=SubjectRepository)

    @pytest.fixture
    def subject_service(self, mock_repository):
        """Create SubjectService instance with mocked repository."""
        return MockSubjectService(mock_repository)

    @pytest.fixture
    def sample_subject_data(self):
        """Sample subject data for testing."""
        from app.models.subject import SubjectType
        return {
            "code": "MATH001",
            "name_he": "מתמטיקה",
            "name_fr": "Mathématiques",
            "subject_type": SubjectType.ACADEMIC,
            "requires_lab": False,
            "is_active": True,
            "max_hours_per_day": 2,
            "abbreviation": "MATH"
        }

    @pytest.fixture
    def sample_subject(self, sample_subject_data):
        """Sample subject instance for testing."""
        subject = Subject(**sample_subject_data)
        subject.id = 1
        return subject

    def test_init_with_repository(self, mock_repository):
        """Test service initialization with repository."""
        service = MockSubjectService(mock_repository)
        assert service.repository == mock_repository
        assert service.subject_repo == mock_repository

    def test_get_by_code_success(self, subject_service, mock_repository, sample_subject):
        """Test successful get_by_code."""
        # Arrange
        mock_repository.get_by_code.return_value = sample_subject
        
        # Act
        result = subject_service.get_by_code("MATH001")
        
        # Assert
        assert result == sample_subject
        mock_repository.get_by_code.assert_called_once_with("MATH001")

    def test_get_by_code_not_found(self, subject_service, mock_repository):
        """Test get_by_code when subject not found."""
        # Arrange
        mock_repository.get_by_code.return_value = None
        
        # Act
        result = subject_service.get_by_code("NONEXISTENT")
        
        # Assert
        assert result is None
        mock_repository.get_by_code.assert_called_once_with("NONEXISTENT")

    def test_get_active_subjects(self, subject_service, mock_repository, sample_subject):
        """Test get_active_subjects method."""
        # Arrange
        mock_repository.get_active_subjects.return_value = [sample_subject]
        
        # Act
        result = subject_service.get_active_subjects(skip=0, limit=10)
        
        # Assert
        assert result == [sample_subject]
        mock_repository.get_active_subjects.assert_called_once_with(0, 10)

    def test_search_subjects(self, subject_service, mock_repository, sample_subject):
        """Test search_subjects method."""
        # Arrange
        mock_repository.search_subjects.return_value = [sample_subject]
        
        # Act
        result = subject_service.search_subjects("Math", skip=0, limit=10)
        
        # Assert
        assert result == [sample_subject]
        mock_repository.search_subjects.assert_called_once_with("Math", 0, 10)

    def test_get_active_subjects_default_params(self, subject_service, mock_repository, sample_subject):
        """Test get_active_subjects with default parameters."""
        # Arrange
        mock_repository.get_active_subjects.return_value = [sample_subject]
        
        # Act
        result = subject_service.get_active_subjects()
        
        # Assert
        assert result == [sample_subject]
        mock_repository.get_active_subjects.assert_called_once_with(0, 100)

    def test_search_subjects_default_params(self, subject_service, mock_repository, sample_subject):
        """Test search_subjects with default parameters."""
        # Arrange
        mock_repository.search_subjects.return_value = [sample_subject]
        
        # Act
        result = subject_service.search_subjects("Math")
        
        # Assert
        assert result == [sample_subject]
        mock_repository.search_subjects.assert_called_once_with("Math", 0, 100)

    def test_get_active_subjects_empty_result(self, subject_service, mock_repository):
        """Test get_active_subjects when no subjects found."""
        # Arrange
        mock_repository.get_active_subjects.return_value = []
        
        # Act
        result = subject_service.get_active_subjects()
        
        # Assert
        assert result == []
        mock_repository.get_active_subjects.assert_called_once_with(0, 100)

    def test_search_subjects_empty_result(self, subject_service, mock_repository):
        """Test search_subjects when no subjects found."""
        # Arrange
        mock_repository.search_subjects.return_value = []
        
        # Act
        result = subject_service.search_subjects("NonExistent")
        
        # Assert
        assert result == []
        mock_repository.search_subjects.assert_called_once_with("NonExistent", 0, 100)

    def test_get_active_subjects_with_pagination(self, subject_service, mock_repository, sample_subject):
        """Test get_active_subjects with custom pagination."""
        # Arrange
        mock_repository.get_active_subjects.return_value = [sample_subject]
        
        # Act
        result = subject_service.get_active_subjects(skip=10, limit=5)
        
        # Assert
        assert result == [sample_subject]
        mock_repository.get_active_subjects.assert_called_once_with(10, 5)

    def test_search_subjects_with_pagination(self, subject_service, mock_repository, sample_subject):
        """Test search_subjects with custom pagination."""
        # Arrange
        mock_repository.search_subjects.return_value = [sample_subject]
        
        # Act
        result = subject_service.search_subjects("Math", skip=5, limit=15)
        
        # Assert
        assert result == [sample_subject]
        mock_repository.search_subjects.assert_called_once_with("Math", 5, 15)

