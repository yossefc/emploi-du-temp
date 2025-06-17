"""
Simple test API for debugging - without authentication.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.teacher import Teacher
from app.models.subject import Subject
from app.config.environments import settings

app = FastAPI(title="Test API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Test API is working"}

@app.get("/api/v1/teachers-test")
async def get_teachers_test(db: Session = Depends(get_db)):
    """Get teachers without authentication."""
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
        return {"error": str(e)}

@app.get("/api/v1/subjects-test")
async def get_subjects_test(db: Session = Depends(get_db)):
    """Get subjects without authentication."""
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
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 