# backend/app/models/associations.py
"""
Tables d'association pour les relations many-to-many.
Ce fichier centralise toutes les tables d'association pour éviter les imports circulaires.
"""

from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.base import Base

# Association entre les enseignants et leurs matières
teacher_subjects = Table(
    'teacher_subjects',
    Base.metadata,
    Column('teacher_id', Integer, ForeignKey('teachers.id', ondelete='CASCADE'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('subjects.id', ondelete='CASCADE'), primary_key=True)
)

# Association entre les classes et leurs matières obligatoires
class_mandatory_subjects = Table(
    'class_mandatory_subjects',
    Base.metadata,
    Column('class_id', Integer, ForeignKey('class_groups.id', ondelete='CASCADE'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('subjects.id', ondelete='CASCADE'), primary_key=True)
)

# Association optionnelle : classes et salles préférées
class_preferred_rooms = Table(
    'class_preferred_rooms',
    Base.metadata,
    Column('class_id', Integer, ForeignKey('class_groups.id', ondelete='CASCADE'), primary_key=True),
    Column('room_id', Integer, ForeignKey('rooms.id', ondelete='CASCADE'), primary_key=True),
    Column('preference_level', Integer, default=1)  # 1=préféré, 2=acceptable, 3=à éviter
)