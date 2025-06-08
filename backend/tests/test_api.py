import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.core.config import settings
from app.db.session import get_db

# Créer une base de données de test en mémoire
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

class TestAuth:
    def test_register_user(self):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpassword123",
                "role": "teacher"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "access_token" in data

    def test_login_user(self):
        # D'abord créer un utilisateur
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "loginpassword123",
                "role": "teacher"
            }
        )
        
        # Ensuite tester le login
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "login@example.com",
                "password": "loginpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

class TestTeachers:
    def setup_method(self):
        # Créer un utilisateur et obtenir un token
        response = client.post(
            "/api/v1/auth/register",
            json={
                    
                    "email": "admin@example.com",
                    "username": "admin",
                    "password": "admin123",
                    "role": "ADMIN"
                    
            }
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_create_teacher(self):
        response = client.post(
            "/api/v1/teachers",
            json={
                "code": "T001",
                "first_name": "Jean",
                "last_name": "Dupont",
                "email": "jean.dupont@school.com",
                "max_hours_per_week": 20,
                "subjects": []
            },
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "T001"
        assert data["first_name"] == "Jean"

    def test_get_teachers(self):
        # Créer un enseignant d'abord
        client.post(
            "/api/v1/teachers",
            json={
                "code": "T002",
                "first_name": "Marie",
                "last_name": "Martin",
                "email": "marie.martin@school.com",
                "max_hours_per_week": 25,
                "subjects": []
            },
            headers=self.headers
        )
        
        response = client.get("/api/v1/teachers", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_update_teacher(self):
        # Créer un enseignant
        create_response = client.post(
            "/api/v1/teachers",
            json={
                "code": "T003",
                "first_name": "Pierre",
                "last_name": "Durand",
                "email": "pierre.durand@school.com",
                "max_hours_per_week": 30,
                "subjects": []
            },
            headers=self.headers
        )
        teacher_id = create_response.json()["id"]
        
        # Mettre à jour l'enseignant
        response = client.put(
            f"/api/v1/teachers/{teacher_id}",
            json={
                "max_hours_per_week": 35
            },
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["max_hours_per_week"] == 35

class TestScheduleGeneration:
    def setup_method(self):
        # Créer un utilisateur admin
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@example.com",
                "username": "adminuser",
                "password": "adminpassword123",
                "role": "admin"
            }
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_generate_schedule(self):
        # D'abord créer les données nécessaires (enseignants, matières, classes, salles)
        # ... (code pour créer les données de test)
        
        # Ensuite générer l'emploi du temps
        response = client.post(
            "/api/v1/schedules/generate",
            json={
                "name": "Test Schedule",
                "parameters": {
                    "max_time_seconds": 30,
                    "optimize_teacher_gaps": True
                }
            },
            headers=self.headers
        )
        assert response.status_code in [200, 202]  # 202 si asynchrone
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["status"] in ["generated", "processing"]

class TestAIAgent:
    def setup_method(self):
        # Créer un utilisateur
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "ai@example.com",
                "username": "aiuser",
                "password": "aipassword123",
                "role": "teacher"
            }
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_parse_constraints(self):
        response = client.post(
            "/api/v1/ai/parse-constraints",
            json={
                "text": "Le professeur Dupont ne peut pas enseigner le vendredi après-midi"
            },
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "constraints" in data
        assert isinstance(data["constraints"], list) 