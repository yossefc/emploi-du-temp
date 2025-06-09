"""
Système de peuplement de données de test pour l'application de génération d'emplois du temps.
Données cohérentes avec le système scolaire israélien.
"""

import random
from datetime import time
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models.user import User, UserRole
from app.models.teacher import Teacher
from app.models.subject import Subject, SubjectType
from app.models.class_group import ClassGroup, Grade, ClassType
from app.models.room import Room, RoomType
from app.models.constraint import (
    DayOfWeek, TeacherAvailability, TeacherPreference, 
    RoomUnavailability, ClassSubjectRequirement, GlobalConstraint,
    ConstraintType
)


# Configuration du hashage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class IsraeliSchoolDataFactory:
    """Factory pour créer des données de test cohérentes avec le système scolaire israélien."""
    
    def __init__(self):
        self.created_users = []
        self.created_teachers = []
        self.created_subjects = []
        self.created_classes = []
        self.created_rooms = []
    
    def create_users(self, db: Session) -> List[User]:
        """Créer les utilisateurs du système."""
        # Vérifier s'il y a déjà des utilisateurs
        existing_count = db.query(User).count()
        if existing_count > 0:
            print(f"   ⚠️  {existing_count} utilisateur(s) déjà présent(s)")
            return []
            
        users_data = [
            {
                "email": "admin@school.edu.il",
                "username": "admin",
                "full_name": "מנהל המערכת",  # System Admin in Hebrew
                "role": UserRole.ADMIN,
                "language_preference": "he"
            },
            {
                "email": "principal@school.edu.il", 
                "username": "principal",
                "full_name": "Sarah Cohen",
                "role": UserRole.ADMIN,
                "language_preference": "fr"
            },
            {
                "email": "coordinator@school.edu.il",
                "username": "coordinator", 
                "full_name": "דוד לוי",  # David Levy in Hebrew
                "role": UserRole.TEACHER,
                "language_preference": "he"
            },
            {
                "email": "secretary@school.edu.il",
                "username": "secretary",
                "full_name": "Marie Dubois",
                "role": UserRole.VIEWER,
                "language_preference": "fr"
            }
        ]
        
        for user_data in users_data:
            user = User(
                email=user_data["email"],
                username=user_data["username"],
                full_name=user_data["full_name"],
                hashed_password=pwd_context.hash("password123"),  # Password par défaut
                role=user_data["role"],
                language_preference=user_data["language_preference"],
                is_active=True
            )
            db.add(user)
            self.created_users.append(user)
        
        db.flush()
        return self.created_users

    def create_subjects(self, db: Session) -> List[Subject]:
        """Créer les matières selon le programme israélien."""
        subjects_data = [
            # Matières obligatoires
            {
                "code": "HEB001",
                "name_he": "עברית",
                "name_fr": "Hébreu",
                "subject_type": SubjectType.LANGUAGE,
                "is_religious": False,
                "max_hours_per_day": 2
            },
            {
                "code": "MATH001", 
                "name_he": "מתמטיקה",
                "name_fr": "Mathématiques",
                "subject_type": SubjectType.ACADEMIC,
                "max_hours_per_day": 2
            },
            {
                "code": "ENG001",
                "name_he": "אנגלית", 
                "name_fr": "Anglais",
                "subject_type": SubjectType.LANGUAGE,
                "max_hours_per_day": 2
            },
            {
                "code": "HIST001",
                "name_he": "תולדות עם ישראל",
                "name_fr": "Histoire du peuple juif",
                "subject_type": SubjectType.ACADEMIC,
                "is_religious": True
            },
            {
                "code": "FRE001",
                "name_he": "צרפתית",
                "name_fr": "Français", 
                "subject_type": SubjectType.LANGUAGE,
                "max_hours_per_day": 2
            },
            
            # Sciences
            {
                "code": "PHYS001",
                "name_he": "פיזיקה",
                "name_fr": "Physique",
                "subject_type": SubjectType.SCIENCE_LAB,
                "requires_lab": True,
                "requires_special_room": True,
                "requires_consecutive_hours": True
            },
            {
                "code": "CHEM001",
                "name_he": "כימיה", 
                "name_fr": "Chimie",
                "subject_type": SubjectType.SCIENCE_LAB,
                "requires_lab": True,
                "requires_special_room": True,
                "requires_consecutive_hours": True
            },
            {
                "code": "BIO001",
                "name_he": "ביולוגיה",
                "name_fr": "Biologie",
                "subject_type": SubjectType.SCIENCE_LAB,
                "requires_lab": True,
                "requires_special_room": True
            },
            {
                "code": "GEO001",
                "name_he": "גיאוגרפיה",
                "name_fr": "Géographie", 
                "subject_type": SubjectType.ACADEMIC
            },
            
            # Matières religieuses
            {
                "code": "TORA001",
                "name_he": "תורה",
                "name_fr": "Torah",
                "subject_type": SubjectType.RELIGIOUS,
                "is_religious": True,
                "requires_gender_separation": True
            },
            {
                "code": "TALM001",
                "name_he": "תלמוד",
                "name_fr": "Talmud",
                "subject_type": SubjectType.RELIGIOUS,
                "is_religious": True,
                "requires_gender_separation": True
            },
            
            # Arts et sports
            {
                "code": "ART001",
                "name_he": "אמנות",
                "name_fr": "Arts plastiques",
                "subject_type": SubjectType.ARTS,
                "requires_special_room": True
            },
            {
                "code": "MUS001",
                "name_he": "מוזיקה",
                "name_fr": "Musique",
                "subject_type": SubjectType.ARTS,
                "requires_special_room": True
            },
            {
                "code": "PE001",
                "name_he": "חינוך גופני",
                "name_fr": "Éducation physique",
                "subject_type": SubjectType.SPORTS,
                "requires_special_room": True,
                "requires_gender_separation": True
            },
            
            # Informatique et technologie
            {
                "code": "CS001",
                "name_he": "מדעי המחשב",
                "name_fr": "Informatique",
                "subject_type": SubjectType.ACADEMIC,
                "requires_special_room": True,
                "requires_consecutive_hours": True
            }
        ]
        
        for subject_data in subjects_data:
            subject = Subject(
                code=subject_data["code"],
                name_he=subject_data["name_he"],
                name_fr=subject_data["name_fr"],
                subject_type=subject_data["subject_type"],
                requires_lab=subject_data.get("requires_lab", False),
                requires_special_room=subject_data.get("requires_special_room", False),
                requires_consecutive_hours=subject_data.get("requires_consecutive_hours", False),
                max_hours_per_day=subject_data.get("max_hours_per_day", 1),
                is_religious=subject_data.get("is_religious", False),
                requires_gender_separation=subject_data.get("requires_gender_separation", False)
            )
            db.add(subject)
            self.created_subjects.append(subject)
        
        db.flush()
        return self.created_subjects

    def create_teachers(self, db: Session) -> List[Teacher]:
        """Créer les enseignants avec spécialités."""
        teachers_data = [
            {
                "code": "T001",
                "first_name": "רחל",  # Rachel
                "last_name": "כהן",   # Cohen  
                "email": "rachel.cohen@school.edu.il",
                "phone": "+972-50-1234567",
                "language": "he",
                "subjects": ["HEB001", "HIST001"]  # Hébreu et Histoire juive
            },
            {
                "code": "T002", 
                "first_name": "David",
                "last_name": "Levy",
                "email": "david.levy@school.edu.il",
                "phone": "+972-52-2345678",
                "language": "he",
                "subjects": ["MATH001"]  # Mathématiques
            },
            {
                "code": "T003",
                "first_name": "Sarah",
                "last_name": "Martin",
                "email": "sarah.martin@school.edu.il", 
                "phone": "+972-54-3456789",
                "language": "fr",
                "subjects": ["FRE001"]  # Français
            },
            {
                "code": "T004",
                "first_name": "יוסף",  # Yosef
                "last_name": "רוזנברג", # Rosenberg
                "email": "yosef.rosenberg@school.edu.il",
                "phone": "+972-50-4567890",
                "language": "he", 
                "subjects": ["PHYS001", "MATH001"]  # Physique et Math
            },
            {
                "code": "T005",
                "first_name": "Marie",
                "last_name": "Dubois",
                "email": "marie.dubois@school.edu.il",
                "phone": "+972-52-5678901",
                "language": "fr",
                "subjects": ["ENG001"]  # Anglais
            },
            {
                "code": "T006",
                "first_name": "אברהם", # Abraham
                "last_name": "גולדשטיין", # Goldstein
                "email": "abraham.goldstein@school.edu.il",
                "phone": "+972-54-6789012",
                "language": "he",
                "subjects": ["TORA001", "TALM001"]  # Torah et Talmud
            },
            {
                "code": "T007",
                "first_name": "מרים", # Miriam
                "last_name": "שפירא", # Shapira
                "email": "miriam.shapira@school.edu.il",
                "phone": "+972-50-7890123",
                "language": "he",
                "subjects": ["CHEM001", "BIO001"]  # Chimie et Biologie
            },
            {
                "code": "T008",
                "first_name": "Pierre",
                "last_name": "Moreau",
                "email": "pierre.moreau@school.edu.il",
                "phone": "+972-52-8901234",
                "language": "fr",
                "subjects": ["GEO001", "HIST001"]  # Géographie et Histoire
            },
            {
                "code": "T009",
                "first_name": "אסתר", # Esther
                "last_name": "בן-דוד", # Ben-David
                "email": "esther.bendavid@school.edu.il",
                "phone": "+972-54-9012345",
                "language": "he",
                "subjects": ["ART001", "MUS001"]  # Arts et Musique
            },
            {
                "code": "T010",
                "first_name": "משה", # Moshe
                "last_name": "כץ", # Katz
                "email": "moshe.katz@school.edu.il",
                "phone": "+972-50-0123456",
                "language": "he",
                "subjects": ["PE001"]  # Éducation physique
            },
            {
                "code": "T011",
                "first_name": "נטע", # Neta
                "last_name": "אבן", # Even
                "email": "neta.even@school.edu.il",
                "phone": "+972-52-1234567",
                "language": "he",
                "subjects": ["CS001"]  # Informatique
            }
        ]
        
        for teacher_data in teachers_data:
            teacher = Teacher(
                code=teacher_data["code"],
                first_name=teacher_data["first_name"],
                last_name=teacher_data["last_name"],
                email=teacher_data["email"],
                phone=teacher_data["phone"],
                primary_language=teacher_data["language"],
                is_active=True,
                max_hours_per_day=6,
                max_hours_per_week=30
            )
            db.add(teacher)
            self.created_teachers.append((teacher, teacher_data["subjects"]))
        
        db.flush()
        return [teacher for teacher, _ in self.created_teachers]

    def create_classes(self, db: Session) -> List[ClassGroup]:
        """Créer les classes selon le système israélien."""
        classes_data = [
            # Classes de collège (7-9)
            {"code": "7A", "name": "כיתה ז1", "grade": Grade.GRADE_7, "student_count": 28, "is_mixed": True},
            {"code": "7B", "name": "כיתה ז2", "grade": Grade.GRADE_7, "student_count": 26, "is_mixed": True},
            {"code": "8A", "name": "כיתה ח1", "grade": Grade.GRADE_8, "student_count": 30, "is_mixed": True},
            {"code": "8B", "name": "כיתה ח2", "grade": Grade.GRADE_8, "student_count": 27, "is_mixed": True},
            {"code": "9A", "name": "כיתה ט1", "grade": Grade.GRADE_9, "student_count": 29, "is_mixed": True},
            {"code": "9B", "name": "כיתה ט2", "grade": Grade.GRADE_9, "student_count": 25, "is_mixed": True},
            
            # Classes de lycée (10-12)
            {"code": "10A", "name": "כיתה י1", "grade": Grade.GRADE_10, "student_count": 24, "class_type": ClassType.ADVANCED},
            {"code": "10B", "name": "כיתה י2", "grade": Grade.GRADE_10, "student_count": 22, "is_mixed": True},
            {"code": "11A", "name": "כיתה יא1", "grade": Grade.GRADE_11, "student_count": 20, "class_type": ClassType.ADVANCED},
            {"code": "11B", "name": "כיתה יא2", "grade": Grade.GRADE_11, "student_count": 18, "is_mixed": True},
            {"code": "12A", "name": "כיתה יב1", "grade": Grade.GRADE_12, "student_count": 19, "class_type": ClassType.ADVANCED},
            {"code": "12B", "name": "כיתה יב2", "grade": Grade.GRADE_12, "student_count": 17, "is_mixed": True}
        ]
        
        for class_data in classes_data:
            class_group = ClassGroup(
                code=class_data["code"],
                name=class_data["name"],
                grade=class_data["grade"],
                class_type=class_data.get("class_type", ClassType.REGULAR),
                student_count=class_data["student_count"],
                is_boys_only=class_data.get("is_boys_only", False),
                is_girls_only=class_data.get("is_girls_only", False),
                is_mixed=class_data.get("is_mixed", True),
                primary_language="he"
            )
            db.add(class_group)
            self.created_classes.append(class_group)
        
        db.flush()
        return self.created_classes

    def create_rooms(self, db: Session) -> List[Room]:
        """Créer les salles de classe et laboratoires."""
        rooms_data = [
            # Salles de classe standard
            {"code": "101", "name": "אולם 101", "room_type": RoomType.REGULAR_CLASSROOM, "capacity": 35},
            {"code": "102", "name": "אולם 102", "room_type": RoomType.REGULAR_CLASSROOM, "capacity": 35},
            {"code": "103", "name": "אולם 103", "room_type": RoomType.REGULAR_CLASSROOM, "capacity": 35},
            {"code": "104", "name": "אולם 104", "room_type": RoomType.REGULAR_CLASSROOM, "capacity": 35},
            {"code": "201", "name": "אולם 201", "room_type": RoomType.REGULAR_CLASSROOM, "capacity": 30},
            {"code": "202", "name": "אולם 202", "room_type": RoomType.REGULAR_CLASSROOM, "capacity": 30},
            {"code": "203", "name": "אולם 203", "room_type": RoomType.REGULAR_CLASSROOM, "capacity": 30},
            {"code": "204", "name": "אולם 204", "room_type": RoomType.REGULAR_CLASSROOM, "capacity": 30},
            
            # Laboratoires
            {"code": "LAB_PHYS", "name": "מעבדת פיזיקה", "room_type": RoomType.SCIENCE_LAB, "capacity": 20},
            {"code": "LAB_CHEM", "name": "מעבדת כימיה", "room_type": RoomType.SCIENCE_LAB, "capacity": 20},
            {"code": "LAB_BIO", "name": "מעבדת ביולוגיה", "room_type": RoomType.SCIENCE_LAB, "capacity": 20},
            {"code": "LAB_CS", "name": "מעבדת מחשבים", "room_type": RoomType.COMPUTER_LAB, "capacity": 25},
            
            # Salles spécialisées
            {"code": "GYM", "name": "אולם התעמלות", "room_type": RoomType.SPORTS_HALL, "capacity": 60},
            {"code": "ART", "name": "חדר אמנות", "room_type": RoomType.ART_ROOM, "capacity": 25},
            {"code": "MUS", "name": "חדר מוזיקה", "room_type": RoomType.MUSIC_ROOM, "capacity": 30},
            {"code": "LIB", "name": "ספרייה", "room_type": RoomType.LIBRARY, "capacity": 40}
        ]
        
        for room_data in rooms_data:
            room = Room(
                code=room_data["code"],
                name=room_data["name"],
                room_type=room_data["room_type"],
                capacity=room_data["capacity"],
                is_active=True,
                has_projector=True,
                has_computers=room_data["room_type"] in [RoomType.COMPUTER_LAB, RoomType.SCIENCE_LAB],
                has_lab_equipment=room_data["room_type"] == RoomType.SCIENCE_LAB,
                has_air_conditioning=True,
                is_accessible=True
            )
            db.add(room)
            self.created_rooms.append(room)
        
        db.flush()
        return self.created_rooms

    def link_teachers_subjects(self, db: Session):
        """Associer les enseignants à leurs matières."""
        subject_map = {subject.code: subject for subject in self.created_subjects}
        
        for teacher, subject_codes in self.created_teachers:
            for subject_code in subject_codes:
                if subject_code in subject_map:
                    teacher.subjects.append(subject_map[subject_code])
        
        db.flush()

    def create_teacher_availabilities(self, db: Session):
        """Créer les disponibilités des enseignants (semaine israélienne)."""
        # Jours de la semaine israélienne (dimanche = 0 à jeudi = 4)
        israeli_weekdays = [DayOfWeek.SUNDAY, DayOfWeek.MONDAY, DayOfWeek.TUESDAY, 
                           DayOfWeek.WEDNESDAY, DayOfWeek.THURSDAY]
        
        for teacher, _ in self.created_teachers:
            for day in israeli_weekdays:
                # Horaires standard : 8h-16h (sauf vendredi)
                if day == DayOfWeek.FRIDAY:
                    # Vendredi court : 8h-13h 
                    availability = TeacherAvailability(
                        teacher_id=teacher.id,
                        day_of_week=day,
                        start_time=time(8, 0),
                        end_time=time(13, 0),
                        is_available=True
                    )
                else:
                    # Jours normaux : 8h-16h
                    availability = TeacherAvailability(
                        teacher_id=teacher.id,
                        day_of_week=day,
                        start_time=time(8, 0),
                        end_time=time(16, 0),
                        is_available=True
                    )
                db.add(availability)
        
        db.flush()

    def create_class_subject_requirements(self, db: Session):
        """Créer les exigences de matières par classe."""
        subject_map = {subject.code: subject for subject in self.created_subjects}
        
        # Matières obligatoires par niveau
        requirements_by_grade = {
            Grade.GRADE_7: [
                ("HEB001", 5), ("MATH001", 5), ("ENG001", 4), ("HIST001", 2),
                ("GEO001", 2), ("ART001", 2), ("PE001", 2), ("TORA001", 3)
            ],
            Grade.GRADE_8: [
                ("HEB001", 5), ("MATH001", 5), ("ENG001", 4), ("HIST001", 2),
                ("GEO001", 2), ("BIO001", 2), ("ART001", 2), ("PE001", 2), ("TORA001", 3)
            ],
            Grade.GRADE_9: [
                ("HEB001", 5), ("MATH001", 5), ("ENG001", 4), ("HIST001", 2),
                ("GEO001", 2), ("BIO001", 2), ("PHYS001", 2), ("PE001", 2), ("TORA001", 3)
            ],
            Grade.GRADE_10: [
                ("HEB001", 4), ("MATH001", 5), ("ENG001", 4), ("HIST001", 3),
                ("PHYS001", 3), ("CHEM001", 3), ("BIO001", 2), ("PE001", 2), ("CS001", 2)
            ],
            Grade.GRADE_11: [
                ("HEB001", 4), ("MATH001", 5), ("ENG001", 4), ("HIST001", 3),
                ("PHYS001", 4), ("CHEM001", 3), ("BIO001", 3), ("CS001", 3)
            ],
            Grade.GRADE_12: [
                ("HEB001", 4), ("MATH001", 5), ("ENG001", 4), ("HIST001", 3),
                ("PHYS001", 4), ("CHEM001", 3), ("BIO001", 3), ("CS001", 3)
            ]
        }
        
        for class_group in self.created_classes:
            grade_requirements = requirements_by_grade.get(class_group.grade, [])
            
            for subject_code, hours_per_week in grade_requirements:
                if subject_code in subject_map:
                    requirement = ClassSubjectRequirement(
                        class_group_id=class_group.id,
                        subject_id=subject_map[subject_code].id,
                        hours_per_week=hours_per_week
                    )
                    db.add(requirement)
        
        db.flush()

    def create_global_constraints(self, db: Session):
        """Créer les contraintes globales de l'école."""
        constraints = [
            {
                "name": "Pause déjeuner",
                "constraint_type": ConstraintType.HARD,
                "description": "Pause déjeuner de 12h à 13h",
                "is_active": True,
                "parameters": {"break_start": "12:00", "break_end": "13:00"}
            },
            {
                "name": "Vendredi court",
                "constraint_type": ConstraintType.HARD,
                "description": "Cours jusqu'à 13h le vendredi",
                "is_active": True,
                "parameters": {"friday_end": "13:00"}
            },
            {
                "name": "Pas de cours le samedi",
                "constraint_type": ConstraintType.HARD,
                "description": "Pas de cours le samedi (Shabbat)",
                "is_active": True,
                "parameters": {"blocked_day": 6}
            },
            {
                "name": "Séparation des sexes - matières religieuses",
                "constraint_type": ConstraintType.SOFT,
                "description": "Classes séparées pour Torah et Talmud",
                "is_active": True,
                "parameters": {"subjects": ["TORA001", "TALM001", "PE001"]}
            }
        ]
        
        for constraint_data in constraints:
            constraint = GlobalConstraint(
                name=constraint_data["name"],
                constraint_type=constraint_data["constraint_type"],
                description=constraint_data["description"],
                is_active=constraint_data["is_active"],
                parameters=constraint_data["parameters"]
            )
            db.add(constraint)
        
        db.flush()


def populate_test_data(db: Session) -> Dict[str, Any]:
    """
    Fonction principale pour peupler la base de données avec des données de test.
    
    Returns:
        Dict avec les statistiques de création
    """
    factory = IsraeliSchoolDataFactory()
    
    print("🏫 Création des données de test pour l'école israélienne...")
    
    # 1. Créer les utilisateurs
    print("👥 Création des utilisateurs...")
    users = factory.create_users(db)
    
    # 2. Créer les matières  
    print("📚 Création des matières...")
    subjects = factory.create_subjects(db)
    
    # 3. Créer les enseignants
    print("👨‍🏫 Création des enseignants...")
    teachers = factory.create_teachers(db)
    
    # 4. Associer enseignants et matières
    print("🔗 Association enseignants-matières...")
    factory.link_teachers_subjects(db)
    
    # 5. Créer les classes
    print("🎓 Création des classes...")
    classes = factory.create_classes(db)
    
    # 6. Créer les salles
    print("🏢 Création des salles...")
    rooms = factory.create_rooms(db)
    
    # 7. Créer les disponibilités
    print("📅 Création des disponibilités...")
    factory.create_teacher_availabilities(db)
    
    # 8. Créer les exigences de matières
    print("📋 Création des exigences...")
    factory.create_class_subject_requirements(db)
    
    # 9. Créer les contraintes globales
    print("⚙️ Création des contraintes...")
    factory.create_global_constraints(db)
    
    # Commit final
    db.commit()
    
    stats = {
        "users": len(users),
        "teachers": len(teachers), 
        "subjects": len(subjects),
        "classes": len(classes),
        "rooms": len(rooms),
        "teacher_subjects": sum(len(t.subjects) for t in teachers),
        "availabilities": len(teachers) * 5,  # 5 jours par semaine
        "class_requirements": db.query(ClassSubjectRequirement).count(),
        "global_constraints": 4
    }
    
    print("✅ Données de test créées avec succès !")
    print(f"📊 Statistiques: {stats}")
    
    return stats


def clear_all_data(db: Session):
    """Vider toutes les données de la base."""
    from sqlalchemy import text
    
    print("🧹 Suppression de toutes les données...")
    
    # Ordre de suppression pour respecter les contraintes FK
    tables_to_clear = [
        "class_subject_requirements",
        "teacher_availabilities", 
        "teacher_preferences",
        "room_unavailabilities",
        "global_constraints",
        "teacher_subjects",
        "schedule_conflicts",
        "schedule_entries",
        "schedules",
        "class_groups",
        "rooms", 
        "subjects",
        "teachers",
        "users"
    ]
    
    for table in tables_to_clear:
        try:
            db.execute(text(f"DELETE FROM {table}"))
        except Exception as e:
            print(f"⚠️ Erreur lors de la suppression de {table}: {e}")
    
    db.commit()
    print("✅ Toutes les données supprimées")