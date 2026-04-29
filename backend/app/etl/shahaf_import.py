"""
Importateur pour les données provenant du système Shahaf.
"""

import json
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from sqlalchemy.orm import Session
from pathlib import Path
import logging

from .base_importer import BaseImporter
from .exceptions import ETLError, ValidationError, ReferenceError, TransformationError
from app.models.teacher import Teacher
from app.models.subject import Subject, SubjectType
from app.models.class_group import ClassGroup, ClassType
from app.models.room import Room, RoomType
from app.models.constraint import (
    TeacherAvailability, TeacherPreference, RoomUnavailability, 
    ClassSubjectRequirement, DayOfWeek
)
from app.models.user import User


logger = logging.getLogger(__name__)


class ShahafImporter(BaseImporter):
    """Importateur pour les données Shahaf."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.subject_mapping = {}  # Cache des matières
        self.room_mapping = {}     # Cache des salles
        self.teacher_mapping = {}  # Cache des enseignants
        self.class_mapping = {}    # Cache des classes
        
    def import_from_json(self, json_path: str) -> Dict[str, Any]:
        """
        Import complet depuis un fichier JSON d'export Shahaf.
        
        Args:
            json_path: Chemin vers le fichier JSON
            
        Returns:
            Résumé de l'import
        """
        self.start_import()
        
        try:
            # Charger les données JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Valider la structure générale
            if not self.validate_data(data):
                raise ValidationError("Structure JSON invalide")
                
            # Import dans l'ordre des dépendances
            self._import_subjects(data.get('subjects', []))
            self._import_rooms(data.get('rooms', []))
            self._import_classes(data.get('classes', []))
            self._import_teachers(data.get('teachers', []))
            self._import_constraints(data.get('constraints', []))
            
            # Valider les références croisées
            if not self._validate_all_references():
                raise ReferenceError("Erreurs de références croisées détectées")
            
            # Vérifier l'intégrité finale
            if not self.check_db_integrity():
                raise ETLError("Erreur d'intégrité de la base de données")
                
            # Commit si tout va bien
            self.commit_import()
            
        except Exception as e:
            self.add_error(ETLError(f"Erreur lors de l'import: {str(e)}"))
            self.rollback_import()
        
        finally:
            self.end_import()
            
        return self.get_import_summary()
    
    def import_from_csv(self, csv_path: str, data_type: str) -> Dict[str, Any]:
        """
        Import depuis un fichier CSV spécifique.
        
        Args:
            csv_path: Chemin vers le fichier CSV
            data_type: Type de données ('teachers', 'subjects', 'classes', 'rooms')
        """
        self.start_import()
        
        try:
            df = pd.read_csv(csv_path)
            
            if data_type == 'teachers':
                self._import_teachers_from_df(df)
            elif data_type == 'subjects':
                self._import_subjects_from_df(df)
            elif data_type == 'classes':
                self._import_classes_from_df(df)
            elif data_type == 'rooms':
                self._import_rooms_from_df(df)
            else:
                raise ValidationError(f"Type de données non supporté: {data_type}")
                
            self.commit_import()
            
        except Exception as e:
            self.add_error(ETLError(f"Erreur lors de l'import CSV: {str(e)}"))
            self.rollback_import()
        
        finally:
            self.end_import()
            
        return self.get_import_summary()
    
    def validate_data(self, data: Any) -> bool:
        """Valide la structure des données d'entrée."""
        if not isinstance(data, dict):
            self.add_error(ValidationError("Les données doivent être un dictionnaire"))
            return False
            
        required_sections = ['subjects', 'rooms', 'classes', 'teachers']
        for section in required_sections:
            if section not in data:
                self.add_warning(f"Section manquante: {section}")
                
        return True
    
    def transform_data(self, data: Any) -> Dict[str, Any]:
        """Transforme les données Shahaf vers le format interne."""
        # Cette méthode sera utilisée pour des transformations spécifiques
        # selon le type de données
        return data
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """Importe les données transformées."""
        # Cette méthode sera utilisée comme point d'entrée principal
        return True
    
    def _import_subjects(self, subjects_data: List[Dict[str, Any]]):
        """Importe les matières."""
        logger.info(f"Import de {len(subjects_data)} matières")
        
        for index, subject_data in enumerate(subjects_data):
            try:
                # Valider les données obligatoires
                if not all(key in subject_data for key in ['code', 'name_he', 'name_fr']):
                    self.add_error(ValidationError(
                        f"Données manquantes pour la matière ligne {index + 1}",
                        line_number=index + 1
                    ))
                    continue
                
                # Transformer les données
                transformed_data = self._transform_subject_data(subject_data)
                
                # Créer ou mettre à jour la matière
                subject, created = self.get_or_create_record(
                    Subject,
                    {"code": transformed_data["code"]},
                    transformed_data
                )
                
                if not created:
                    # Mise à jour des champs
                    for key, value in transformed_data.items():
                        setattr(subject, key, value)
                
                self.subject_mapping[subject.code] = subject
                self.import_log["successful_imports"] += 1
                
            except Exception as e:
                self.add_error(ETLError(
                    f"Erreur lors de l'import de la matière: {str(e)}",
                    line_number=index + 1,
                    data=subject_data
                ))
        
        self.import_log["total_records"] += len(subjects_data)
    
    def _import_rooms(self, rooms_data: List[Dict[str, Any]]):
        """Importe les salles."""
        logger.info(f"Import de {len(rooms_data)} salles")
        
        for index, room_data in enumerate(rooms_data):
            try:
                # Valider les données obligatoires
                if not all(key in room_data for key in ['code', 'name', 'capacity']):
                    self.add_error(ValidationError(
                        f"Données manquantes pour la salle ligne {index + 1}",
                        line_number=index + 1
                    ))
                    continue
                
                # Transformer les données
                transformed_data = self._transform_room_data(room_data)
                
                # Créer ou mettre à jour la salle
                room, created = self.get_or_create_record(
                    Room,
                    {"code": transformed_data["code"]},
                    transformed_data
                )
                
                if not created:
                    # Mise à jour des champs
                    for key, value in transformed_data.items():
                        setattr(room, key, value)
                
                self.room_mapping[room.code] = room
                self.import_log["successful_imports"] += 1
                
            except Exception as e:
                self.add_error(ETLError(
                    f"Erreur lors de l'import de la salle: {str(e)}",
                    line_number=index + 1,
                    data=room_data
                ))
        
        self.import_log["total_records"] += len(rooms_data)
    
    def _import_classes(self, classes_data: List[Dict[str, Any]]):
        """Importe les classes."""
        logger.info(f"Import de {len(classes_data)} classes")
        
        for index, class_data in enumerate(classes_data):
            try:
                # Valider les données obligatoires
                if not all(key in class_data for key in ['code', 'name', 'grade_level', 'student_count']):
                    self.add_error(ValidationError(
                        f"Données manquantes pour la classe ligne {index + 1}",
                        line_number=index + 1
                    ))
                    continue
                
                # Transformer les données
                transformed_data = self._transform_class_data(class_data)
                
                # Créer ou mettre à jour la classe
                class_group, created = self.get_or_create_record(
                    ClassGroup,
                    {"code": transformed_data["code"]},
                    transformed_data
                )
                
                if not created:
                    # Mise à jour des champs
                    for key, value in transformed_data.items():
                        setattr(class_group, key, value)
                
                self.class_mapping[class_group.code] = class_group
                self.import_log["successful_imports"] += 1
                
            except Exception as e:
                self.add_error(ETLError(
                    f"Erreur lors de l'import de la classe: {str(e)}",
                    line_number=index + 1,
                    data=class_data
                ))
        
        self.import_log["total_records"] += len(classes_data)
    
    def _import_teachers(self, teachers_data: List[Dict[str, Any]]):
        """Importe les enseignants."""
        logger.info(f"Import de {len(teachers_data)} enseignants")
        
        for index, teacher_data in enumerate(teachers_data):
            try:
                # Valider les données obligatoires
                if not all(key in teacher_data for key in ['code', 'first_name', 'last_name']):
                    self.add_error(ValidationError(
                        f"Données manquantes pour l'enseignant ligne {index + 1}",
                        line_number=index + 1
                    ))
                    continue
                
                # Transformer les données
                transformed_data = self._transform_teacher_data(teacher_data)
                
                # Créer ou mettre à jour l'enseignant
                teacher, created = self.get_or_create_record(
                    Teacher,
                    {"code": transformed_data["code"]},
                    transformed_data
                )
                
                if not created:
                    # Mise à jour des champs
                    for key, value in transformed_data.items():
                        if key != 'subjects':  # Les relations seront traitées séparément
                            setattr(teacher, key, value)
                
                # Gérer les relations avec les matières
                if 'subjects' in teacher_data:
                    self._assign_teacher_subjects(teacher, teacher_data['subjects'])
                
                # Gérer les disponibilités
                if 'availabilities' in teacher_data:
                    self._import_teacher_availabilities(teacher, teacher_data['availabilities'])
                
                self.teacher_mapping[teacher.code] = teacher
                self.import_log["successful_imports"] += 1
                
            except Exception as e:
                self.add_error(ETLError(
                    f"Erreur lors de l'import de l'enseignant: {str(e)}",
                    line_number=index + 1,
                    data=teacher_data
                ))
        
        self.import_log["total_records"] += len(teachers_data)
    
    def _import_constraints(self, constraints_data: List[Dict[str, Any]]):
        """Importe les contraintes."""
        logger.info(f"Import de {len(constraints_data)} contraintes")
        
        for index, constraint_data in enumerate(constraints_data):
            try:
                constraint_type = constraint_data.get('type')
                
                if constraint_type == 'class_subject_requirement':
                    self._import_class_subject_requirement(constraint_data)
                elif constraint_type == 'room_unavailability':
                    self._import_room_unavailability(constraint_data)
                elif constraint_type == 'teacher_preference':
                    self._import_teacher_preference(constraint_data)
                else:
                    self.add_warning(f"Type de contrainte non supporté: {constraint_type}")
                
                self.import_log["successful_imports"] += 1
                
            except Exception as e:
                self.add_error(ETLError(
                    f"Erreur lors de l'import de la contrainte: {str(e)}",
                    line_number=index + 1,
                    data=constraint_data
                ))
        
        self.import_log["total_records"] += len(constraints_data)
    
    def _transform_subject_data(self, subject_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforme les données de matière Shahaf vers le format interne."""
        # Mapping des types de matières Shahaf vers nos types
        type_mapping = {
            'academic': SubjectType.ACADEMIC,
            'sport': SubjectType.SPORTS,
            'art': SubjectType.ARTS,
            'religious': SubjectType.RELIGIOUS,
            'language': SubjectType.LANGUAGE,
            'lab': SubjectType.SCIENCE_LAB
        }
        
        return {
            'code': subject_data['code'].upper(),
            'name_he': subject_data['name_he'],
            'name_fr': subject_data['name_fr'],
            'subject_type': type_mapping.get(subject_data.get('type', 'academic'), SubjectType.ACADEMIC),
            'requires_lab': subject_data.get('requires_lab', False),
            'requires_special_room': subject_data.get('requires_special_room', False),
            'requires_consecutive_hours': subject_data.get('requires_consecutive_hours', False),
            'max_hours_per_day': subject_data.get('max_hours_per_day', 2),
            'is_religious': subject_data.get('is_religious', False),
            'requires_gender_separation': subject_data.get('requires_gender_separation', False),
            'color_hex': subject_data.get('color_hex'),
            'abbreviation': subject_data.get('abbreviation')
        }
    
    def _transform_room_data(self, room_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforme les données de salle Shahaf vers le format interne."""
        # Mapping des types de salles
        type_mapping = {
            'classroom': RoomType.REGULAR_CLASSROOM,
            'lab': RoomType.SCIENCE_LAB,
            'computer_lab': RoomType.COMPUTER_LAB,
            'gym': RoomType.SPORTS_HALL,
            'art_room': RoomType.ART_ROOM,
            'music_room': RoomType.MUSIC_ROOM,
            'library': RoomType.LIBRARY,
            'prayer_room': RoomType.PRAYER_ROOM,
            'auditorium': RoomType.AUDITORIUM
        }
        
        return {
            'code': room_data['code'].upper(),
            'name': room_data['name'],
            'capacity': int(room_data['capacity']),
            'room_type': type_mapping.get(room_data.get('type', 'classroom'), RoomType.REGULAR_CLASSROOM),
            'building': room_data.get('building'),
            'floor': room_data.get('floor'),
            'has_projector': room_data.get('has_projector', False),
            'has_computers': room_data.get('has_computers', False),
            'has_lab_equipment': room_data.get('has_lab_equipment', False),
            'has_air_conditioning': room_data.get('has_air_conditioning', True),
            'is_accessible': room_data.get('is_accessible', True),
            'suitable_for_prayer': room_data.get('suitable_for_prayer', False),
            'gender_restricted': room_data.get('gender_restricted'),
            'description': room_data.get('description')
        }
    
    def _transform_class_data(self, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforme les données de classe Shahaf vers le format interne."""
        # Mapping des types de classes
        type_mapping = {
            'regular': ClassType.REGULAR,
            'advanced': ClassType.ADVANCED,
            'special_needs': ClassType.SPECIAL_NEEDS
        }
        
        return {
            'code': class_data['code'].upper(),
            'name': class_data['name'],
            'grade_level': str(class_data['grade_level']),
            'student_count': int(class_data['student_count']),
            'class_type': type_mapping.get(class_data.get('type', 'regular'), ClassType.REGULAR),
            'is_boys_only': class_data.get('is_boys_only', False),
            'is_girls_only': class_data.get('is_girls_only', False),
            'is_mixed': class_data.get('is_mixed', True),
            'primary_language': class_data.get('primary_language', 'he'),
            'description': class_data.get('description'),
            'academic_year': class_data.get('academic_year', '2024-2025')
        }
    
    def _transform_teacher_data(self, teacher_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforme les données d'enseignant Shahaf vers le format interne."""
        return {
            'code': teacher_data['code'].upper(),
            'first_name': teacher_data['first_name'],
            'last_name': teacher_data['last_name'],
            'email': teacher_data.get('email'),
            'phone': teacher_data.get('phone'),
            'max_hours_per_week': teacher_data.get('max_hours_per_week', 30),
            'max_hours_per_day': teacher_data.get('max_hours_per_day', 8),
            'prefers_consecutive_hours': teacher_data.get('prefers_consecutive_hours', True),
            'primary_language': teacher_data.get('primary_language', 'he'),
            'can_teach_in_french': teacher_data.get('can_teach_in_french', False),
            'can_teach_in_hebrew': teacher_data.get('can_teach_in_hebrew', True),
            'contract_type': teacher_data.get('contract_type', 'full_time'),
            'notes': teacher_data.get('notes')
        }
    
    def _assign_teacher_subjects(self, teacher: Teacher, subjects_list: List[str]):
        """Assigne les matières à un enseignant."""
        # Vider les matières existantes
        teacher.subjects.clear()
        
        # Ajouter les nouvelles matières
        for subject_code in subjects_list:
            if subject_code in self.subject_mapping:
                teacher.subjects.append(self.subject_mapping[subject_code])
            else:
                self.add_warning(f"Matière non trouvée: {subject_code} pour l'enseignant {teacher.code}")
    
    def _import_teacher_availabilities(self, teacher: Teacher, availabilities: List[Dict[str, Any]]):
        """Importe les disponibilités d'un enseignant."""
        # Supprimer les disponibilités existantes
        self.db.query(TeacherAvailability).filter_by(teacher_id=teacher.id).delete()
        
        for availability in availabilities:
            try:
                day_mapping = {
                    'sunday': DayOfWeek.SUNDAY,
                    'monday': DayOfWeek.MONDAY,
                    'tuesday': DayOfWeek.TUESDAY,
                    'wednesday': DayOfWeek.WEDNESDAY,
                    'thursday': DayOfWeek.THURSDAY,
                    'friday': DayOfWeek.FRIDAY
                }
                
                teacher_availability = TeacherAvailability(
                    teacher_id=teacher.id,
                    day_of_week=day_mapping[availability['day']],
                    start_time=availability['start_time'],
                    end_time=availability['end_time'],
                    is_available=availability.get('is_available', True),
                    notes=availability.get('notes')
                )
                
                self.db.add(teacher_availability)
                
            except Exception as e:
                self.add_error(ETLError(f"Erreur lors de l'import de disponibilité: {str(e)}"))
    
    def _import_class_subject_requirement(self, constraint_data: Dict[str, Any]):
        """Importe une exigence de matière pour une classe."""
        try:
            class_code = constraint_data['class_code']
            subject_code = constraint_data['subject_code']
            
            if class_code not in self.class_mapping:
                raise ReferenceError(f"Classe non trouvée: {class_code}")
            
            if subject_code not in self.subject_mapping:
                raise ReferenceError(f"Matière non trouvée: {subject_code}")
            
            class_group = self.class_mapping[class_code]
            subject = self.subject_mapping[subject_code]
            
            # Vérifier si l'exigence existe déjà
            existing = self.db.query(ClassSubjectRequirement).filter_by(
                class_id=class_group.id,
                subject_id=subject.id
            ).first()
            
            if existing:
                # Mise à jour
                existing.hours_per_week = constraint_data.get('hours_per_week', existing.hours_per_week)
                existing.is_mandatory = constraint_data.get('is_mandatory', existing.is_mandatory)
                existing.requires_double_period = constraint_data.get('requires_double_period', existing.requires_double_period)
                existing.max_per_day = constraint_data.get('max_per_day', existing.max_per_day)
            else:
                # Création
                requirement = ClassSubjectRequirement(
                    class_id=class_group.id,
                    subject_id=subject.id,
                    hours_per_week=constraint_data.get('hours_per_week', 1),
                    is_mandatory=constraint_data.get('is_mandatory', True),
                    requires_double_period=constraint_data.get('requires_double_period', False),
                    max_per_day=constraint_data.get('max_per_day', 2)
                )
                self.db.add(requirement)
                
        except Exception as e:
            raise ETLError(f"Erreur lors de l'import d'exigence classe-matière: {str(e)}")
    
    def _import_room_unavailability(self, constraint_data: Dict[str, Any]):
        """Importe une indisponibilité de salle."""
        try:
            room_code = constraint_data['room_code']
            
            if room_code not in self.room_mapping:
                raise ReferenceError(f"Salle non trouvée: {room_code}")
            
            room = self.room_mapping[room_code]
            
            day_mapping = {
                'sunday': DayOfWeek.SUNDAY,
                'monday': DayOfWeek.MONDAY,
                'tuesday': DayOfWeek.TUESDAY,
                'wednesday': DayOfWeek.WEDNESDAY,
                'thursday': DayOfWeek.THURSDAY,
                'friday': DayOfWeek.FRIDAY
            }
            
            unavailability = RoomUnavailability(
                room_id=room.id,
                day_of_week=day_mapping[constraint_data['day']],
                start_time=constraint_data['start_time'],
                end_time=constraint_data['end_time'],
                reason=constraint_data.get('reason'),
                is_recurring=constraint_data.get('is_recurring', True)
            )
            
            self.db.add(unavailability)
            
        except Exception as e:
            raise ETLError(f"Erreur lors de l'import d'indisponibilité de salle: {str(e)}")
    
    def _import_teacher_preference(self, constraint_data: Dict[str, Any]):
        """Importe une préférence d'enseignant."""
        try:
            teacher_code = constraint_data['teacher_code']
            
            if teacher_code not in self.teacher_mapping:
                raise ReferenceError(f"Enseignant non trouvé: {teacher_code}")
            
            teacher = self.teacher_mapping[teacher_code]
            
            preference = TeacherPreference(
                teacher_id=teacher.id,
                preference_type=constraint_data['preference_type'],
                parameters=constraint_data.get('parameters', {}),
                weight=constraint_data.get('weight', 1),
                description=constraint_data.get('description'),
                is_active=constraint_data.get('is_active', True)
            )
            
            self.db.add(preference)
            
        except Exception as e:
            raise ETLError(f"Erreur lors de l'import de préférence d'enseignant: {str(e)}")
    
    def _validate_all_references(self) -> bool:
        """Valide toutes les références croisées."""
        is_valid = True
        
        # Valider les références des enseignants vers les matières
        for teacher_code, teacher in self.teacher_mapping.items():
            for subject in teacher.subjects:
                if subject.code not in self.subject_mapping:
                    self.add_error(ReferenceError(f"Référence invalide: enseignant {teacher_code} -> matière {subject.code}"))
                    is_valid = False
        
        # Valider les références des contraintes
        # Cette validation sera complétée selon les besoins
        
        return is_valid
    
    def _import_teachers_from_df(self, df: pd.DataFrame):
        """Importe les enseignants depuis un DataFrame."""
        teachers_data = []
        
        for _, row in df.iterrows():
            teacher_dict = {
                'code': row.get('code', ''),
                'first_name': row.get('first_name', ''),
                'last_name': row.get('last_name', ''),
                'email': row.get('email', ''),
                'phone': row.get('phone', ''),
                'max_hours_per_week': row.get('max_hours_per_week', 30),
                'max_hours_per_day': row.get('max_hours_per_day', 8),
                'primary_language': row.get('primary_language', 'he'),
                'can_teach_in_french': row.get('can_teach_in_french', False),
                'can_teach_in_hebrew': row.get('can_teach_in_hebrew', True),
                'contract_type': row.get('contract_type', 'full_time'),
                'notes': row.get('notes', '')
            }
            
            # Traiter les matières (supposées être séparées par des virgules)
            subjects_str = row.get('subjects', '')
            if subjects_str:
                teacher_dict['subjects'] = [s.strip() for s in subjects_str.split(',')]
            
            teachers_data.append(teacher_dict)
        
        self._import_teachers(teachers_data)
    
    def _import_subjects_from_df(self, df: pd.DataFrame):
        """Importe les matières depuis un DataFrame."""
        subjects_data = []
        
        for _, row in df.iterrows():
            subject_dict = {
                'code': row.get('code', ''),
                'name_he': row.get('name_he', ''),
                'name_fr': row.get('name_fr', ''),
                'type': row.get('type', 'academic'),
                'requires_lab': row.get('requires_lab', False),
                'requires_special_room': row.get('requires_special_room', False),
                'requires_consecutive_hours': row.get('requires_consecutive_hours', False),
                'max_hours_per_day': row.get('max_hours_per_day', 2),
                'is_religious': row.get('is_religious', False),
                'requires_gender_separation': row.get('requires_gender_separation', False),
                'color_hex': row.get('color_hex', ''),
                'abbreviation': row.get('abbreviation', '')
            }
            subjects_data.append(subject_dict)
        
        self._import_subjects(subjects_data)
    
    def _import_classes_from_df(self, df: pd.DataFrame):
        """Importe les classes depuis un DataFrame."""
        classes_data = []
        
        for _, row in df.iterrows():
            class_dict = {
                'code': row.get('code', ''),
                'name': row.get('name', ''),
                'grade_level': row.get('grade_level', ''),
                'student_count': row.get('student_count', 0),
                'type': row.get('type', 'regular'),
                'is_boys_only': row.get('is_boys_only', False),
                'is_girls_only': row.get('is_girls_only', False),
                'is_mixed': row.get('is_mixed', True),
                'primary_language': row.get('primary_language', 'he'),
                'description': row.get('description', ''),
                'academic_year': row.get('academic_year', '2024-2025')
            }
            classes_data.append(class_dict)
        
        self._import_classes(classes_data)
    
    def _import_rooms_from_df(self, df: pd.DataFrame):
        """Importe les salles depuis un DataFrame."""
        rooms_data = []
        
        for _, row in df.iterrows():
            room_dict = {
                'code': row.get('code', ''),
                'name': row.get('name', ''),
                'capacity': row.get('capacity', 0),
                'type': row.get('type', 'classroom'),
                'building': row.get('building', ''),
                'floor': row.get('floor', 0),
                'has_projector': row.get('has_projector', False),
                'has_computers': row.get('has_computers', False),
                'has_lab_equipment': row.get('has_lab_equipment', False),
                'has_air_conditioning': row.get('has_air_conditioning', True),
                'is_accessible': row.get('is_accessible', True),
                'suitable_for_prayer': row.get('suitable_for_prayer', False),
                'gender_restricted': row.get('gender_restricted', ''),
                'description': row.get('description', '')
            }
            rooms_data.append(room_dict)
        
        self._import_rooms(rooms_data) 