
# backend/app/schemas/class_group.py

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class ClassType(str, Enum):
    """Types de classes."""
    REGULAR = "regular"
    ADVANCED = "advanced"
    SPECIAL_NEEDS = "special_needs"


class ClassGroupBase(BaseModel):
    """Schema de base pour les classes."""
    code: str = Field(..., min_length=1, max_length=20, description="Code unique de la classe")
    name: str = Field(..., min_length=1, max_length=255, description="Nom de la classe")  # Ancien: nom
    grade_name: str = Field(..., min_length=1, max_length=50, description="Niveau scolaire")  # Ancien: niveau
    student_count: int = Field(..., ge=1, le=50, description="Nombre d'élèves")  # Ancien: effectif
    class_type: ClassType = Field(default=ClassType.REGULAR, description="Type de classe")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    academic_year: Optional[str] = Field(None, max_length=20, description="Année scolaire")
    preferred_schedules: Optional[Dict[str, Any]] = Field(None, description="Préférences horaires")  # Ancien: horaires_preferes
    is_boys_only: bool = Field(default=False, description="Classe garçons uniquement")
    is_girls_only: bool = Field(default=False, description="Classe filles uniquement")
    is_mixed: bool = Field(default=True, description="Classe mixte")
    primary_language: str = Field(default="he", pattern="^(he|fr)$", description="Langue principale")
    homeroom_teacher_id: Optional[int] = Field(None, description="ID du professeur principal")
    is_active: bool = Field(default=True, description="Statut actif")
    
    @validator('code')
    def validate_code(cls, v):
        if not v.strip():
            raise ValueError('Le code de classe ne peut pas être vide')
        return v.strip().upper()
    
    @validator('is_mixed')
    def validate_gender_settings(cls, v, values):
        """Valide la cohérence des paramètres de genre."""
        is_boys = values.get('is_boys_only', False)
        is_girls = values.get('is_girls_only', False)
        
        if is_boys and is_girls:
            raise ValueError('Une classe ne peut pas être à la fois garçons et filles uniquement')
        
        if (is_boys or is_girls) and v:
            raise ValueError('Une classe non-mixte ne peut pas être marquée comme mixte')
        
        return v
    
    @validator('student_count')
    def validate_student_count(cls, v):
        if v < 1 or v > 50:
            raise ValueError('Le nombre d\'élèves doit être entre 1 et 50')
        return v


class ClassGroupCreate(ClassGroupBase):
    """Schema pour la création de classe."""
    subject_ids: Optional[List[int]] = Field(None, description="IDs des matières obligatoires")


class ClassGroupUpdate(BaseModel):
    """Schema pour la mise à jour de classe."""
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    grade_name: Optional[str] = Field(None, min_length=1, max_length=50)
    student_count: Optional[int] = Field(None, ge=1, le=50)
    class_type: Optional[ClassType] = None
    description: Optional[str] = None
    academic_year: Optional[str] = Field(None, max_length=20)
    preferred_schedules: Optional[Dict[str, Any]] = None
    is_boys_only: Optional[bool] = None
    is_girls_only: Optional[bool] = None
    is_mixed: Optional[bool] = None
    primary_language: Optional[str] = Field(None, pattern="^(he|fr)$")
    homeroom_teacher_id: Optional[int] = None
    is_active: Optional[bool] = None


class ClassGroupResponse(ClassGroupBase):
    """Schema de réponse pour une classe."""
    id: int
    homeroom_teacher: Optional['TeacherBasic'] = None
    mandatory_subjects: List['SubjectBasic'] = []
    total_required_hours: int = Field(description="Total d'heures requises par semaine")
    
    class Config:
        from_attributes = True


# Import des schemas liés pour éviter les références circulaires
from app.schemas.teacher import TeacherBasic
from app.schemas.subject import SubjectBasic

# Reconstruction des modèles pour gérer les références forward
ClassGroupResponse.model_rebuild()