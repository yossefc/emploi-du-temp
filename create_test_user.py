#!/usr/bin/env python3
"""
Script pour créer un utilisateur de test.
"""

import os
import sys

# Ajouter le chemin du backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session
from backend.app.db.base import SessionLocal, engine, Base
from backend.app.models.user import User, UserRole
from backend.app.core.auth import get_password_hash

def create_test_user():
    """Créer un utilisateur de test."""
    
    # Créer les tables
    Base.metadata.create_all(bind=engine)
    
    # Créer une session
    db: Session = SessionLocal()
    
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("L'utilisateur admin existe déjà")
            return
        
        # Créer l'utilisateur admin
        admin_user = User(
            email="admin@example.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="Administrateur",
            role=UserRole.ADMIN,
            is_active=True,
            language_preference="fr"
        )
        
        db.add(admin_user)
        
        # Créer un utilisateur enseignant
        teacher_user = User(
            email="teacher@example.com", 
            username="teacher",
            hashed_password=get_password_hash("teacher123"),
            full_name="Enseignant Test",
            role=UserRole.TEACHER,
            is_active=True,
            language_preference="fr"
        )
        
        db.add(teacher_user)
        db.commit()
        
        print("✅ Utilisateurs créés avec succès !")
        print("👤 Admin: username=admin, password=admin123")
        print("👤 Teacher: username=teacher, password=teacher123")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user() 