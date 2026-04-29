"""
Exceptions personnalisées pour le module ETL.
"""

from typing import Optional, Dict, Any


class ETLError(Exception):
    """Exception de base pour les erreurs ETL."""
    def __init__(self, message: str, line_number: Optional[int] = None, data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.line_number = line_number
        self.data = data or {}
    
    def __str__(self):
        if self.line_number:
            return f"Ligne {self.line_number}: {self.message}"
        return self.message


class ValidationError(ETLError):
    """Erreur de validation des données."""
    pass


class TransformationError(ETLError):
    """Erreur lors de la transformation des données."""
    pass


class ReferenceError(ETLError):
    """Erreur de référence croisée."""
    pass


class ImportError(ETLError):
    """Erreur lors de l'import en base de données."""
    pass 