"""
Pytest configuration and fixtures for comprehensive testing.

This module provides all necessary fixtures for testing the School Timetable Generator:
- Database fixtures (engine, session) with in-memory SQLite
- FastAPI test client with dependency overrides
- Test user and authentication helpers
- Complete test data fixtures (teachers, subjects, classes, rooms)
- Helper functions for creating test objects and authentication
"""

import pytest
from datetime import datetime, date, timedelta
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Import application components
from app.main import app
from app.db.base import Base, get_db
from app.core.auth import get_password_hash, create_access_token
from app.core.config import settings

# Import all models to register them with Base
from app.models.user import User, UserRole
from app.models.teacher import Teacher, teacher_subjects
from app.models.subject import Subject, SubjectType
from app.models.class_group import ClassGroup, Grade, ClassType
from app.models.room import Room, RoomType
from app.models.schedule import Schedule, ScheduleEntry
from app.models.constraint import (
    DayOfWeek, ConstraintType, TeacherAvailability, 
    ClassSubjectRequirement
)


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def engine():
    """Create SQLite in-memory engine for testing."""
    test_engine = create_engine(
        "sqlite:///:memory:",  # In-memory database
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine
    
    # Cleanup
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test with automatic rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    
    # Create session bound to connection
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def override_get_db(session: Session):
    """Create dependency override function for get_db."""
    def _get_db_override():
        try:
            yield session
        finally:
            pass
    return _get_db_override


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create TestClient with database dependency override."""
    app.dependency_overrides[get_db] = override_get_db(db_session)
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up overrides
    app.dependency_overrides.clear()


# =============================================================================
# USER AND AUTHENTICATION FIXTURES
# =============================================================================

@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user for authentication."""
    user = User(
        email="test@school.edu",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        role=UserRole.ADMIN,
        is_active=True,
        language_preference="he"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_teacher_user(db_session: Session) -> User:
    """Create a test user with teacher role."""
    user = User(
        email="teacher@school.edu",
        username="teacheruser",
        hashed_password=get_password_hash("teacherpass123"),
        full_name="Teacher User",
        role=UserRole.TEACHER,
        is_active=True,
        language_preference="he"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for API requests."""
    access_token = create_access_token(
        data={"sub": test_user.username, "user_id": test_user.id}
    )
    return {"Authorization": f"Bearer {access_token}"}


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================

@pytest.fixture
def test_subjects(db_session: Session) -> list[Subject]:
    """Create test subjects."""
    subjects = [
        Subject(
            code="MATH101",
            name_he="מתמטיקה",
            name_fr="Mathématiques",
            subject_type=SubjectType.ACADEMIC,
            color_hex="#FF5733",
            abbreviation="MATH",
            requires_lab=False,
            max_hours_per_day=2,
            is_active=True
        ),
        Subject(
            code="SCI101",
            name_he="מדעים",
            name_fr="Sciences",
            subject_type=SubjectType.SCIENCE_LAB,
            color_hex="#33FF57",
            abbreviation="SCI",
            requires_lab=True,
            requires_special_room=True,
            max_hours_per_day=2,
            is_active=True
        ),
        Subject(
            code="HEB101",
            name_he="עברית",
            name_fr="Hébreu",
            subject_type=SubjectType.LANGUAGE,
            color_hex="#3357FF",
            abbreviation="HEB",
            requires_lab=False,
            max_hours_per_day=2,
            is_active=True
        ),
        Subject(
            code="PE101",
            name_he="חינוך גופני",
            name_fr="Éducation physique",
            subject_type=SubjectType.SPORTS,
            color_hex="#FF33F5",
            abbreviation="PE",
            requires_special_room=True,
            max_hours_per_day=1,
            is_active=True
        )
    ]
    
    for subject in subjects:
        db_session.add(subject)
    
    db_session.commit()
    
    for subject in subjects:
        db_session.refresh(subject)
    
    return subjects


@pytest.fixture
def test_teachers(db_session: Session, test_subjects: list[Subject]) -> list[Teacher]:
    """Create test teachers with subject assignments."""
    teachers = [
        Teacher(
            code="T001",
            first_name="יוסי",
            last_name="כהן",
            email="yossi.cohen@school.edu",
            phone="054-123-4567",
            max_hours_per_week=25,
            max_hours_per_day=6,
            hire_date=date(2020, 9, 1),
            contract_type="full_time",
            primary_language="he",
            can_teach_in_hebrew=True,
            can_teach_in_french=False,
            is_active=True
        ),
        Teacher(
            code="T002",
            first_name="מרים",
            last_name="לוי",
            email="miriam.levy@school.edu",
            phone="054-987-6543",
            max_hours_per_week=30,
            max_hours_per_day=7,
            hire_date=date(2019, 9, 1),
            contract_type="full_time",
            primary_language="he",
            can_teach_in_hebrew=True,
            can_teach_in_french=True,
            is_active=True
        ),
        Teacher(
            code="T003",
            first_name="דוד",
            last_name="אברהם",
            email="david.abraham@school.edu",
            phone="054-555-1234",
            max_hours_per_week=20,
            max_hours_per_day=5,
            hire_date=date(2021, 9, 1),
            contract_type="part_time",
            primary_language="he",
            can_teach_in_hebrew=True,
            can_teach_in_french=False,
            is_active=True
        )
    ]
    
    for teacher in teachers:
        db_session.add(teacher)
    
    db_session.commit()
    
    # Assign subjects to teachers
    teachers[0].subjects = [test_subjects[0]]  # Math teacher
    teachers[1].subjects = [test_subjects[1]]  # Science teacher
    teachers[2].subjects = [test_subjects[2], test_subjects[3]]  # Hebrew & PE teacher
    
    db_session.commit()
    
    for teacher in teachers:
        db_session.refresh(teacher)
    
    return teachers


@pytest.fixture
def test_rooms(db_session: Session) -> list[Room]:
    """Create test rooms."""
    rooms = [
        Room(
            code="A101",
            name="כיתה רגילה א",
            capacity=30,
            room_type=RoomType.REGULAR_CLASSROOM,
            building="בניין ראשי",
            floor=1,
            has_projector=True,
            has_air_conditioning=True,
            is_accessible=True,
            is_active=True
        ),
        Room(
            code="LAB1",
            name="מעבדת מדעים",
            capacity=25,
            room_type=RoomType.SCIENCE_LAB,
            building="בניין ראשי",
            floor=2,
            has_projector=True,
            has_lab_equipment=True,
            has_air_conditioning=True,
            requires_supervision=True,
            is_accessible=True,
            is_active=True
        ),
        Room(
            code="GYM1",
            name="אולם ספורט",
            capacity=50,
            room_type=RoomType.SPORTS_HALL,
            building="בניין ספורט",
            floor=0,
            has_air_conditioning=False,
            is_accessible=True,
            is_active=True
        ),
        Room(
            code="A201",
            name="כיתה רגילה ב",
            capacity=28,
            room_type=RoomType.REGULAR_CLASSROOM,
            building="בניין ראשי",
            floor=2,
            has_projector=True,
            has_air_conditioning=True,
            is_accessible=True,
            is_active=True
        )
    ]
    
    for room in rooms:
        db_session.add(room)
    
    db_session.commit()
    
    for room in rooms:
        db_session.refresh(room)
    
    return rooms


@pytest.fixture
def test_class_groups(db_session: Session, test_subjects: list[Subject], test_teachers: list[Teacher]) -> list[ClassGroup]:
    """Create test class groups."""
    class_groups = [
        ClassGroup(
            code="9A",
            name="כיתה ט'א",
            grade_level="9",
            student_count=25,
            class_type=ClassType.REGULAR,
            is_mixed=True,
            primary_language="he",
            homeroom_teacher_id=test_teachers[0].id,
            is_active=True
        ),
        ClassGroup(
            code="9B",
            name="כיתה ט'ב",
            grade_level="9",
            student_count=27,
            class_type=ClassType.ADVANCED,
            is_mixed=True,
            primary_language="he",
            homeroom_teacher_id=test_teachers[1].id,
            is_active=True
        ),
        ClassGroup(
            code="10A",
            name="כיתה י'א",
            grade_level="10",
            student_count=23,
            class_type=ClassType.REGULAR,
            is_mixed=True,
            primary_language="he",
            homeroom_teacher_id=test_teachers[2].id,
            is_active=True
        )
    ]
    
    for class_group in class_groups:
        db_session.add(class_group)
    
    db_session.commit()
    
    # Assign subjects to class groups
    for class_group in class_groups:
        class_group.subjects = test_subjects[:3]  # Math, Science, Hebrew
    
    db_session.commit()
    
    for class_group in class_groups:
        db_session.refresh(class_group)
    
    return class_groups


@pytest.fixture
def test_data(test_subjects: list[Subject], test_teachers: list[Teacher], 
              test_rooms: list[Room], test_class_groups: list[ClassGroup]) -> dict:
    """Complete test data fixture with all entities."""
    return {
        "subjects": test_subjects,
        "teachers": test_teachers,
        "rooms": test_rooms,
        "class_groups": test_class_groups
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_test_teacher(db_session: Session, **kwargs) -> Teacher:
    """
    Helper function to create a test teacher with custom attributes.
    
    Args:
        db_session: Database session
        **kwargs: Custom attributes to override defaults
        
    Returns:
        Created Teacher instance
    """
    defaults = {
        "code": f"T{datetime.now().strftime('%H%M%S')}",
        "first_name": "יוחנן",
        "last_name": "דוגמה",
        "email": f"teacher{datetime.now().strftime('%H%M%S')}@school.edu",
        "phone": "054-000-0000",
        "max_hours_per_week": 25,
        "max_hours_per_day": 6,
        "hire_date": date.today(),
        "contract_type": "full_time",
        "primary_language": "he",
        "can_teach_in_hebrew": True,
        "can_teach_in_french": False,
        "is_active": True
    }
    
    # Override defaults with provided kwargs
    defaults.update(kwargs)
    
    teacher = Teacher(**defaults)
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    
    return teacher


def create_test_schedule(db_session: Session, name: str = None, test_data: dict = None) -> Schedule:
    """
    Helper function to create a test schedule with entries.
    
    Args:
        db_session: Database session
        name: Schedule name (optional)
        test_data: Test data dictionary with teachers, subjects, etc.
        
    Returns:
        Created Schedule instance
    """
    if name is None:
        name = f"Test Schedule {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    schedule = Schedule(
        name=name,
        description="Test schedule for automated testing",
        academic_year="2024-2025",
        semester=1,
        status="draft",
        is_active=False,
        solver_status="optimal",
        generation_time_seconds=1.5
    )
    
    db_session.add(schedule)
    db_session.commit()
    db_session.refresh(schedule)
    
    # Add some sample schedule entries if test_data is provided
    if test_data:
        subjects = test_data.get("subjects", [])
        teachers = test_data.get("teachers", [])
        rooms = test_data.get("rooms", [])
        class_groups = test_data.get("class_groups", [])
        
        if all([subjects, teachers, rooms, class_groups]):
            # Create a few sample entries
            entries = [
                ScheduleEntry(
                    schedule_id=schedule.id,
                    day_of_week=0,  # Sunday
                    period=1,
                    class_group_id=class_groups[0].id,
                    subject_id=subjects[0].id,
                    teacher_id=teachers[0].id,
                    room_id=rooms[0].id,
                    is_double_period=False
                ),
                ScheduleEntry(
                    schedule_id=schedule.id,
                    day_of_week=1,  # Monday
                    period=2,
                    class_group_id=class_groups[1].id,
                    subject_id=subjects[1].id,
                    teacher_id=teachers[1].id,
                    room_id=rooms[1].id,
                    is_double_period=True
                )
            ]
            
            for entry in entries:
                db_session.add(entry)
            
            db_session.commit()
    
    return schedule


def authenticate_client(client: TestClient, username: str = "testuser", password: str = "testpassword123") -> dict:
    """
    Helper function to authenticate a test client and return headers.
    
    Args:
        client: FastAPI TestClient
        username: Username for authentication
        password: Password for authentication
        
    Returns:
        Dictionary with Authorization header
    """
    # Login to get access token
    login_data = {"username": username, "password": password}
    response = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    else:
        # If login fails, create token manually (for testing)
        # This assumes we have a test user in the database
        access_token = create_access_token(data={"sub": username, "user_id": 1})
        return {"Authorization": f"Bearer {access_token}"}


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """Configure pytest settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as requiring authentication"
    )


# =============================================================================
# ADDITIONAL FIXTURES FOR SPECIFIC SCENARIOS
# =============================================================================

@pytest.fixture
def empty_db_session(engine) -> Generator[Session, None, None]:
    """Create an empty database session without any test data."""
    connection = engine.connect()
    transaction = connection.begin()
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def authenticated_client(client: TestClient, auth_headers: dict) -> TestClient:
    """Pre-authenticated test client."""
    client.headers.update(auth_headers)
    return client 