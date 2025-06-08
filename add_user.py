#!/usr/bin/env python3
"""
Script simple pour ajouter un utilisateur de test.
"""

import os
import sys
from pathlib import Path

# Définir les variables d'environnement
os.environ["DATABASE_URL"] = "sqlite:///./school_timetable.db"
os.environ["SECRET_KEY"] = "dev-secret-key-123"
os.environ["USE_CLAUDE"] = "false"

# Ajouter le chemin du backend au PYTHONPATH
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from app.core.auth import get_password_hash
    from sqlalchemy import create_engine, text
    
    # Créer la connexion SQLite
    engine = create_engine("sqlite:///./backend/school_timetable.db")
    
    # Créer la table users si elle n'existe pas
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR UNIQUE NOT NULL,
                username VARCHAR UNIQUE NOT NULL,
                hashed_password VARCHAR NOT NULL,
                full_name VARCHAR,
                role VARCHAR DEFAULT 'viewer' NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                language_preference VARCHAR(2) DEFAULT 'he',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """))
        
        # Vérifier si l'utilisateur admin existe
        result = conn.execute(text("SELECT COUNT(*) FROM users WHERE username = 'admin'"))
        if result.scalar() > 0:
            print("L'utilisateur admin existe déjà")
        else:
            # Ajouter l'utilisateur admin
            hashed_password = get_password_hash("admin123")
            conn.execute(text("""
                INSERT INTO users (email, username, hashed_password, full_name, role, is_active, language_preference)
                VALUES (:email, :username, :hashed_password, :full_name, :role, :is_active, :language_preference)
            """), {
                "email": "admin@example.com",
                "username": "admin", 
                "hashed_password": hashed_password,
                "full_name": "Administrateur",
                "role": "admin",
                "is_active": True,
                "language_preference": "fr"
            })
            print("✅ Utilisateur admin créé")
        
        # Vérifier si l'utilisateur teacher existe
        result = conn.execute(text("SELECT COUNT(*) FROM users WHERE username = 'teacher'"))
        if result.scalar() > 0:
            print("L'utilisateur teacher existe déjà")
        else:
            # Ajouter l'utilisateur teacher
            hashed_password = get_password_hash("teacher123")
            conn.execute(text("""
                INSERT INTO users (email, username, hashed_password, full_name, role, is_active, language_preference)
                VALUES (:email, :username, :hashed_password, :full_name, :role, :is_active, :language_preference)
            """), {
                "email": "teacher@example.com",
                "username": "teacher",
                "hashed_password": hashed_password, 
                "full_name": "Enseignant Test",
                "role": "teacher",
                "is_active": True,
                "language_preference": "fr"
            })
            print("✅ Utilisateur teacher créé")
        
        conn.commit()
        
    print("\n🎉 Configuration terminée !")
    print("Vous pouvez maintenant vous connecter avec :")
    print("👤 Username: admin | Password: admin123")
    print("👤 Username: teacher | Password: teacher123")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc() 