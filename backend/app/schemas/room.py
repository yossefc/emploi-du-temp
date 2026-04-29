# backend/app/schemas/room.py

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class RoomType(str, Enum):
    """Types de salles."""
    CLASSROOM = "classroom"
    LAB = "lab"
    GYM = "gym"
    MUSIC = "music"
    ART = "art"
    COMPUTER = "computer"
    LIBRARY = "library"
    AUDITORIUM = "auditorium"


class RoomBase(BaseModel):
    """Schema de base pour les salles."""
    code: str = Field(..., min_length=1, max_length=20, description="Code unique de la salle")
    name: str = Field(..., min_length=1, max_length=255, description="Nom de la salle")
    capacity: int = Field(..., ge=1, le=200, description="Capacité de la salle")  # Ancien: capacite
    type: RoomType = Field(default=RoomType.CLASSROOM, description="Type de salle")
    building: Optional[str] = Field(None, max_length=100, description="Bâtiment")
    floor: Optional[int] = Field(None, ge=-2, le=20, description="Étage")
    equipment: Optional[Dict[str, Any]] = Field(None, description="Équipements disponibles")
    is_accessible: bool = Field(default=True, description="Accessible aux handicapés")
    has_air_conditioning: bool = Field(default=True, description="Climatisation")
    has_windows: bool = Field(default=True, description="Fenêtres")
    is_active: bool = Field(default=True, description="Statut actif")
    
    @validator('code')
    def validate_code(cls, v):
        if not v.strip():
            raise ValueError('Le code de salle ne peut pas être vide')
        return v.strip().upper()
    
    @validator('capacity')
    def validate_capacity(cls, v):
        if v < 1 or v > 200:
            raise ValueError('La capacité doit être entre 1 et 200')
        return v
    
    @validator('equipment')
    def validate_equipment(cls, v):
        """Valide le format des équipements."""
        if v is not None:
            # Vérifier que c'est bien un dictionnaire
            if not isinstance(v, dict):
                raise ValueError('Les équipements doivent être un dictionnaire')
            
            # Valider certains équipements connus
            known_equipment = ['projector', 'whiteboard', 'computers', 'piano', 'lab_equipment']
            for key in v:
                if key not in known_equipment:
                    # Accepter quand même mais logger un warning
                    print(f"Équipement inconnu: {key}")
        
        return v


class RoomCreate(RoomBase):
    """Schema pour la création de salle."""
    pass


class RoomUpdate(BaseModel):
    """Schema pour la mise à jour de salle."""
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    capacity: Optional[int] = Field(None, ge=1, le=200)
    type: Optional[RoomType] = None
    building: Optional[str] = Field(None, max_length=100)
    floor: Optional[int] = Field(None, ge=-2, le=20)
    equipment: Optional[Dict[str, Any]] = None
    is_accessible: Optional[bool] = None
    has_air_conditioning: Optional[bool] = None
    has_windows: Optional[bool] = None
    is_active: Optional[bool] = None


class RoomResponse(RoomBase):
    """Schema de réponse pour une salle."""
    id: int
    is_lab: bool = Field(description="Indique si c'est un laboratoire")
    is_gym: bool = Field(description="Indique si c'est un gymnase")
    has_computers: bool = Field(description="Indique si la salle a des ordinateurs")
    
    class Config:
        from_attributes = True
        
    @validator('is_lab', pre=False, always=True)
    def compute_is_lab(cls, v, values):
        return values.get('type') == RoomType.LAB
    
    @validator('is_gym', pre=False, always=True)
    def compute_is_gym(cls, v, values):
        return values.get('type') == RoomType.GYM
    
    @validator('has_computers', pre=False, always=True)
    def compute_has_computers(cls, v, values):
        if values.get('type') == RoomType.COMPUTER:
            return True
        equipment = values.get('equipment', {})
        return equipment.get('computers', 0) > 0 if equipment else False
