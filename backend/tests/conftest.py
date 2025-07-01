"""
Pytest configuration and fixtures for the entire test suite.
"""
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import get_db, Base
from app.main import app


# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def test_db():
    """Create test database and tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    """Create a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_teacher_data():
    """Sample teacher data for testing."""
    return {
        "code": "T001",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@school.edu",
        "phone": "123-456-7890",
        "department": "Mathematics",
        "hire_date": "2020-01-01",
        "contract_type": "FULL_TIME",
        "is_active": True,
        "language_preference": "ENGLISH",
        "notes": "Experienced math teacher"
    }


@pytest.fixture
def sample_subject_data():
    """Sample subject data for testing."""
    return {
        "code": "MATH101",
        "name_en": "Algebra I",
        "name_he": "אלגברה א",
        "hours_per_week": 5,
        "subject_type": "CORE",
        "grade_levels": [9, 10],
        "language": "ENGLISH",
        "color_hex": "#FF5733",
        "abbreviation": "ALG1",
        "is_active": True
    }


@pytest.fixture
def sample_room_data():
    """Sample room data for testing."""
    return {
        "code": "R101",
        "name": "Math Classroom 1",
        "building": "Main Building",
        "floor": 1,
        "capacity": 30,
        "room_type": "CLASSROOM",
        "equipment": ["PROJECTOR", "WHITEBOARD"],
        "is_accessible": True,
        "is_active": True
    }


@pytest.fixture
def sample_class_group_data():
    """Sample class group data for testing."""
    return {
        "code": "9A",
        "name": "Grade 9 Class A",
        "grade_level": 9,
        "student_count": 25,
        "language": "ENGLISH",
        "gender_type": "MIXED",
        "is_active": True
    } 