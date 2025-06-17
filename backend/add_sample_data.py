#!/usr/bin/env python3
"""
Script pour ajouter des données d'exemple à la base de données.
"""

import sys
from pathlib import Path

# Ajouter le répertoire backend au PATH Python
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.teacher import Teacher
from app.models.subject import Subject
from app.models.class_group import ClassGroup
from app.models.room import Room

DATABASE_URL = "sqlite:///./school_timetable.db"

def add_sample_data():
    """Ajoute des données d'exemple."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    print("📝 Ajout de données d'exemple...")
    
    with SessionLocal() as db:
        try:
            # Vérifier s'il y a déjà des données
            if db.query(User).count() > 0:
                print("⚠️  Des données existent déjà. Suppression...")
                db.query(User).delete()
                db.query(Teacher).delete()
                db.query(Subject).delete()
                db.query(ClassGroup).delete()
                db.query(Room).delete()
                db.commit()
            
            # Créer un utilisateur admin
            admin_user = User(
                username="admin",
                email="admin@example.com",
                is_active=True
            )
            admin_user.set_password("admin123")
            db.add(admin_user)
            db.flush()  # Pour obtenir l'ID
            print("✅ Utilisateur admin créé")
            
            # Créer des matières
            subjects = [
                Subject(name_fr="Mathématiques", name_he="מתמטיקה", code="MATH"),
                Subject(name_fr="Français", name_he="צרפתית", code="FR"),
                Subject(name_fr="Histoire", name_he="היסטוריה", code="HIST"),
                Subject(name_fr="Sciences", name_he="מדעים", code="SCI"),
                Subject(name_fr="Anglais", name_he="אנגלית", code="ENG"),
                Subject(name_fr="Hébreu", name_he="עברית", code="HE"),
                Subject(name_fr="Education Physique", name_he="חינוך גופני", code="PE"),
            ]
            db.add_all(subjects)
            db.flush()  # Pour obtenir les IDs
            print("✅ Matières créées")
            
            # Créer des salles
            rooms = [
                Room(code="A101", nom="Salle A101", capacite=30, type_salle="classroom"),
                Room(code="A102", nom="Salle A102", capacite=25, type_salle="classroom"),
                Room(code="LAB1", nom="Laboratoire 1", capacite=20, type_salle="laboratory"),
                Room(code="INFO1", nom="Salle informatique", capacite=20, type_salle="computer"),
                Room(code="B201", nom="Salle B201", capacite=35, type_salle="classroom"),
                Room(code="GYM", nom="Gymnase", capacite=50, type_salle="gym"),
            ]
            db.add_all(rooms)
            db.flush()
            print("✅ Salles créées")
            
            # Créer des classes
            classes = [
                ClassGroup(code="6E1", nom="6ème 1", niveau="6", effectif=28, primary_language="fr"),
                ClassGroup(code="5E2", nom="5ème 2", niveau="5", effectif=25, primary_language="fr"),
                ClassGroup(code="4E1", nom="4ème 1", niveau="4", effectif=30, primary_language="fr"),
                ClassGroup(code="Y1", nom="י׳ 1", niveau="10", effectif=22, primary_language="he"),
                ClassGroup(code="H2", nom="ח׳ 2", niveau="8", effectif=26, primary_language="he"),
            ]
            db.add_all(classes)
            db.flush()
            print("✅ Classes créées")
            
            # Créer des enseignants
            teachers = [
                Teacher(
                    code="T001",
                    first_name="Jean",
                    last_name="Dupont",
                    email="jean.dupont@school.com",
                    max_hours_per_week=25,
                    primary_language="fr"
                ),
                Teacher(
                    code="T002",
                    first_name="Marie",
                    last_name="Martin",
                    email="marie.martin@school.com",
                    max_hours_per_week=20,
                    primary_language="fr"
                ),
                Teacher(
                    code="T003",
                    first_name="Sarah",
                    last_name="Cohen",
                    email="sarah.cohen@school.com",
                    max_hours_per_week=18,
                    primary_language="he"
                ),
                Teacher(
                    code="T004",
                    first_name="David",
                    last_name="Levy",
                    email="david.levy@school.com",
                    max_hours_per_week=22,
                    primary_language="he"
                ),
                Teacher(
                    code="T005",
                    first_name="Emma",
                    last_name="Dubois",
                    email="emma.dubois@school.com",
                    max_hours_per_week=15,
                    primary_language="fr"
                ),
            ]
            db.add_all(teachers)
            db.flush()
            print("✅ Enseignants créés")
            
            # Associer les matières aux enseignants
            # Jean Dupont - Mathématiques
            math_subject = next(s for s in subjects if s.code == "MATH")
            jean = next(t for t in teachers if t.code == "T001")
            jean.subjects.append(math_subject)
            
            # Marie Martin - Français
            fr_subject = next(s for s in subjects if s.code == "FR")
            marie = next(t for t in teachers if t.code == "T002")
            marie.subjects.append(fr_subject)
            
            # Sarah Cohen - Histoire et Hébreu
            hist_subject = next(s for s in subjects if s.code == "HIST")
            he_subject = next(s for s in subjects if s.code == "HE")
            sarah = next(t for t in teachers if t.code == "T003")
            sarah.subjects.extend([hist_subject, he_subject])
            
            # David Levy - Sciences
            sci_subject = next(s for s in subjects if s.code == "SCI")
            david = next(t for t in teachers if t.code == "T004")
            david.subjects.append(sci_subject)
            
            # Emma Dubois - Anglais et Education Physique
            eng_subject = next(s for s in subjects if s.code == "ENG")
            pe_subject = next(s for s in subjects if s.code == "PE")
            emma = next(t for t in teachers if t.code == "T005")
            emma.subjects.extend([eng_subject, pe_subject])
            
            db.commit()
            print("✅ Relations enseignants-matières créées")
            
            print("\n🎉 Données d'exemple ajoutées avec succès !")
            print(f"   - {len(subjects)} matières")
            print(f"   - {len(classes)} classes")
            print(f"   - {len(rooms)} salles")
            print(f"   - {len(teachers)} enseignants")
            print(f"   - 1 utilisateur admin (admin/admin123)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout des données : {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return False

if __name__ == "__main__":
    print("🚀 Ajout de données d'exemple...")
    print("=" * 50)
    
    if add_sample_data():
        print("\n🎉 Succès ! Vous pouvez maintenant :")
        print("  1. Redémarrer le serveur backend")
        print("  2. Vous connecter avec admin/admin123")
        print("  3. Voir les vraies données dans l'interface")
    else:
        print("\n❌ Échec de l'ajout des données") 