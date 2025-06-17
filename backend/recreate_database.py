#!/usr/bin/env python3
"""
Script pour recréer la base de données avec toutes les tables nécessaires.
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire backend au PATH Python
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.db.base import Base
from app.models import *  # Import tous les modèles

DATABASE_URL = "sqlite:///./school_timetable.db"

def recreate_database():
    """Recrée la base de données avec toutes les tables."""
    
    print("🗑️  Suppression de l'ancienne base de données...")
    db_path = Path("school_timetable.db")
    if db_path.exists():
        try:
            db_path.unlink()
            print("✅ Ancienne base supprimée")
        except Exception as e:
            print(f"❌ Erreur lors de la suppression : {e}")
            return False
    
    print("🔧 Création du moteur de base de données...")
    engine = create_engine(DATABASE_URL, echo=True)
    
    print("📋 Création de toutes les tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées avec succès")
        
        # Vérifier les tables créées
        with engine.connect() as connection:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            print(f"📊 Tables créées : {', '.join(tables)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables : {e}")
        return False

def add_sample_data():
    """Ajoute des données d'exemple."""
    from sqlalchemy.orm import sessionmaker
    from app.models.user import User
    from app.models.teacher import Teacher
    from app.models.subject import Subject
    from app.models.class_group import ClassGroup
    from app.models.room import Room
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    print("📝 Ajout de données d'exemple...")
    
    with SessionLocal() as db:
        try:
            # Créer un utilisateur admin
            admin_user = User(
                username="admin",
                email="admin@example.com",
                is_active=True
            )
            admin_user.set_password("admin123")
            db.add(admin_user)
            
            # Créer des matières
            subjects = [
                Subject(name="Mathématiques", name_he="מתמטיקה", code="MATH"),
                Subject(name="Français", name_he="צרפתית", code="FR"),
                Subject(name="Histoire", name_he="היסטוריה", code="HIST"),
                Subject(name="Sciences", name_he="מדעים", code="SCI"),
                Subject(name="Anglais", name_he="אנגלית", code="ENG"),
            ]
            db.add_all(subjects)
            db.flush()  # Pour obtenir les IDs
            
            # Créer des classes
            classes = [
                ClassGroup(name="6e1", name_he="ו1", grade_level="6", language="fr"),
                ClassGroup(name="5e2", name_he="ה2", grade_level="5", language="fr"),
                ClassGroup(name="4e1", name_he="ד1", grade_level="4", language="fr"),
                ClassGroup(name="י1", name_he="י1", grade_level="10", language="he"),
                ClassGroup(name="ח2", name_he="ח2", grade_level="8", language="he"),
            ]
            db.add_all(classes)
            db.flush()
            
            # Créer des salles
            rooms = [
                Room(name="A101", capacity=30, room_type="classroom"),
                Room(name="A102", capacity=25, room_type="classroom"),
                Room(name="Lab1", capacity=20, room_type="laboratory"),
                Room(name="Info1", capacity=20, room_type="computer"),
                Room(name="B201", capacity=35, room_type="classroom"),
            ]
            db.add_all(rooms)
            db.flush()
            
            # Créer des enseignants
            teachers = [
                Teacher(
                    code="T001",
                    first_name="Jean",
                    last_name="Dupont",
                    email="jean.dupont@school.com",
                    max_hours_per_week=25,
                    primary_language="fr",
                    subjects=[subjects[0]]  # Mathématiques
                ),
                Teacher(
                    code="T002",
                    first_name="Marie",
                    last_name="Martin",
                    email="marie.martin@school.com",
                    max_hours_per_week=20,
                    primary_language="fr",
                    subjects=[subjects[1]]  # Français
                ),
                Teacher(
                    code="T003",
                    first_name="Sarah",
                    last_name="Cohen",
                    email="sarah.cohen@school.com",
                    max_hours_per_week=18,
                    primary_language="he",
                    subjects=[subjects[2]]  # Histoire
                ),
            ]
            db.add_all(teachers)
            
            db.commit()
            print("✅ Données d'exemple ajoutées")
            print(f"   - {len(subjects)} matières")
            print(f"   - {len(classes)} classes")
            print(f"   - {len(rooms)} salles")
            print(f"   - {len(teachers)} enseignants")
            print(f"   - 1 utilisateur admin (admin/admin123)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout des données : {e}")
            db.rollback()
            return False

if __name__ == "__main__":
    print("🚀 Recréation de la base de données...")
    print("=" * 50)
    
    if recreate_database():
        print("\n📦 Ajout de données d'exemple...")
        if add_sample_data():
            print("\n🎉 Base de données recréée avec succès !")
            print("\nVous pouvez maintenant :")
            print("  1. Redémarrer le serveur backend")
            print("  2. Vous connecter avec admin/admin123")
            print("  3. Utiliser la fonctionnalité d'importation")
        else:
            print("\n⚠️  Base créée mais erreur lors de l'ajout des données")
    else:
        print("\n❌ Échec de la recréation de la base de données") 