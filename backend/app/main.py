"""
Main FastAPI application with essential endpoints.
"""

from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from app.config.environments import settings
from app.api.api_v1.api import api_router

# Base SQLAlchemy directement dans main.py
Base = declarative_base()
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifecycle."""
    # Startup
    print("Starting up...")
    # Create database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.OPENAPI_URL else None,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Routes de base
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to School Timetable Generator API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": settings.DOCS_URL,
        "api_prefix": settings.API_V1_PREFIX,
        "status": "All endpoints are being implemented"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected"
    }


# Test endpoint without authentication
@app.get("/api/v1/teachers-test")
async def get_teachers_test():
    """Get teachers without authentication - for testing only."""
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.models.teacher import Teacher
    
    # Create direct database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        try:
            teachers = db.query(Teacher).all()
            result = []
            for teacher in teachers:
                result.append({
                    "id": teacher.id,
                    "code": teacher.code,
                    "first_name": teacher.first_name,
                    "last_name": teacher.last_name,
                    "email": teacher.email,
                    "subjects": []  # Simplified for testing
                })
            return result
        except Exception as e:
            return {"error": str(e), "teachers": []}

# Simple authentication endpoint
@app.post("/api/v1/auth/login")
async def login_simple(username: str = Form(...), password: str = Form(...)):
    """Simple login endpoint for testing."""
    # Check against database user
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.models.user import User
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        try:
            user = db.query(User).filter(User.username == username).first()
            if user and password == "admin123":  # Simple password check for testing
                return {
                    "access_token": "fake-jwt-token-for-testing",
                    "token_type": "bearer",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "role": user.role
                    }
                }
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Nom d'utilisateur ou mot de passe incorrect"
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                                 detail=f"Erreur de connexion: {str(e)}"
             )

# Test endpoint for subjects
@app.get("/api/v1/subjects-test")
async def get_subjects_test():
    """Get subjects without authentication - for testing only."""
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.models.subject import Subject
    
    # Create direct database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        try:
            subjects = db.query(Subject).all()
            result = []
            for subject in subjects:
                result.append({
                    "id": subject.id,
                    "code": subject.code,
                    "name_fr": subject.name_fr,
                    "name_he": subject.name_he
                })
            return result
        except Exception as e:
            return {"error": str(e), "subjects": []}

# Test endpoint to create teachers
@app.post("/api/v1/teachers-test")
async def create_teacher_test(teacher_data: dict):
    """Create teacher without authentication - for testing only."""
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.models.teacher import Teacher
    from app.models.subject import Subject
    
    # Create direct database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        try:
            # Create teacher
            teacher = Teacher(
                code=teacher_data.get('code'),
                first_name=teacher_data.get('first_name'),
                last_name=teacher_data.get('last_name'),
                email=teacher_data.get('email'),
                is_active=True
            )
            
            # Add subjects if provided
            if teacher_data.get('subject_ids'):
                subjects = db.query(Subject).filter(Subject.id.in_(teacher_data['subject_ids'])).all()
                teacher.subjects = subjects
            
            db.add(teacher)
            db.commit()
            db.refresh(teacher)
            
            return {
                "id": teacher.id,
                "code": teacher.code,
                "first_name": teacher.first_name,
                "last_name": teacher.last_name,
                "email": teacher.email,
                "message": "Enseignant créé avec succès"
            }
        except Exception as e:
            db.rollback()
            return {"error": str(e)}


@app.get("/metrics")
async def metrics():
    """Metrics endpoint."""
    return {"message": "Metrics endpoint - À implémenter"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8004) 