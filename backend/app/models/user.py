"""User — comptes utilisateurs, multi-tenant."""

import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base_mixin import TimestampMixin


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"      # plateforme entière (cross-écoles)
    SCHOOL_ADMIN = "school_admin"    # admin d'une école
    TEACHER = "teacher"              # enseignant (lié à un Teacher)
    VIEWER = "viewer"                # lecture seule (parent, élève)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # NULL uniquement pour SUPER_ADMIN
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    language_preference = Column(String(5), default="fr", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Si l'utilisateur est aussi un enseignant
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True, unique=True)

    school = relationship("School", back_populates="users")
    teacher = relationship("Teacher", back_populates="user", uselist=False)
