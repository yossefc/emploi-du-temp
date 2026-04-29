# backend/app/models/room.py

from sqlalchemy import Column, Integer, String, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from enum import Enum as PyEnum


class RoomType(str, PyEnum):
    """Types de salles."""
    CLASSROOM = "classroom"
    LAB = "lab"
    GYM = "gym"
    MUSIC = "music"
    ART = "art"
    COMPUTER = "computer"
    LIBRARY = "library"
    AUDITORIUM = "auditorium"


class Room(Base):
    """Modèle pour les salles."""
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Champ renommé
    capacity = Column(Integer, nullable=False)  # Ancien: capacite
    
    type = Column(Enum(RoomType), default=RoomType.CLASSROOM)
    building = Column(String(100))
    floor = Column(Integer)
    
    # Équipements disponibles (JSON)
    equipment = Column(JSON)  # {"projector": true, "computers": 30, "whiteboard": true}
    
    # Caractéristiques spéciales
    is_accessible = Column(Boolean, default=True)  # Accès handicapés
    has_air_conditioning = Column(Boolean, default=True)
    has_windows = Column(Boolean, default=True)
    
    # Disponibilité
    is_active = Column(Boolean, default=True)
    
    # Relations
    unavailabilities = relationship(
        "RoomUnavailability", 
        back_populates="room",
        cascade="all, delete-orphan"
    )
    
    schedule_entries = relationship(
        "ScheduleEntry", 
        back_populates="room"
    )
    
    @property
    def is_lab(self) -> bool:
        """Vérifie si c'est un laboratoire."""
        return self.type == RoomType.LAB  # type: ignore
    
    @property
    def is_gym(self) -> bool:
        """Vérifie si c'est un gymnase."""
        return self.type == RoomType.GYM  # type: ignore
    
    @property
    def has_computers(self) -> bool:
        """Vérifie si la salle a des ordinateurs."""
        return self.type == RoomType.COMPUTER or (  # type: ignore
            self.equipment and self.equipment.get('computers', 0) > 0
        )
    
    def can_accommodate(self, student_count: int) -> bool:
        """Vérifie si la salle peut accueillir le nombre d'étudiants."""
        return self.capacity >= student_count  # type: ignore
    
    def __repr__(self):
        return f"<Room {self.code}: {self.name} (capacity: {self.capacity})>"