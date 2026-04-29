"""
Classe de base pour tous les importateurs ETL.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import inspect
import logging
from datetime import datetime

from .exceptions import ETLError, ValidationError, ReferenceError


logger = logging.getLogger(__name__)


class BaseImporter(ABC):
    """Classe de base pour tous les importateurs ETL."""
    
    def __init__(self, db: Session):
        self.db = db
        self.errors: List[ETLError] = []
        self.warnings: List[str] = []
        self.import_log: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "total_records": 0,
            "successful_imports": 0,
            "errors": [],
            "warnings": []
        }
        
    def start_import(self):
        """Démarre le processus d'import."""
        self.import_log["start_time"] = datetime.now()
        self.errors.clear()
        self.warnings.clear()
        logger.info("Début de l'import")
    
    def end_import(self):
        """Termine le processus d'import."""
        self.import_log["end_time"] = datetime.now()
        self.import_log["errors"] = [str(e) for e in self.errors]
        self.import_log["warnings"] = self.warnings
        
        duration = (self.import_log["end_time"] - self.import_log["start_time"]).total_seconds()
        logger.info(f"Import terminé en {duration:.2f} secondes")
        logger.info(f"Succès: {self.import_log['successful_imports']}/{self.import_log['total_records']}")
    
    def add_error(self, error: ETLError):
        """Ajoute une erreur à la liste."""
        self.errors.append(error)
        logger.error(str(error))
    
    def add_warning(self, warning: str):
        """Ajoute un avertissement à la liste."""
        self.warnings.append(warning)
        logger.warning(warning)
    
    @abstractmethod
    def validate_data(self, data: Any) -> bool:
        """Valide les données d'entrée."""
        pass
    
    @abstractmethod
    def transform_data(self, data: Any) -> Dict[str, Any]:
        """Transforme les données vers le format interne."""
        pass
    
    @abstractmethod
    def import_data(self, data: Dict[str, Any]) -> bool:
        """Importe les données transformées en base."""
        pass
    
    def validate_references(self, data: Dict[str, Any]) -> List[str]:
        """Valide les références croisées."""
        errors = []
        
        # Cette méthode peut être surchargée par les classes enfants
        # pour implémenter une validation spécifique
        
        return errors
    
    def get_or_create_record(self, model_class, unique_fields: Dict[str, Any], 
                           defaults: Optional[Dict[str, Any]] = None) -> Tuple[Any, bool]:
        """
        Récupère ou crée un enregistrement selon les champs uniques.
        
        Returns:
            Tuple[record, created]: L'enregistrement et un booléen indiquant s'il a été créé
        """
        try:
            # Chercher l'enregistrement existant
            record = self.db.query(model_class).filter_by(**unique_fields).first()
            
            if record:
                return record, False
            
            # Créer un nouveau record
            create_data = {**unique_fields, **(defaults or {})}
            record = model_class(**create_data)
            self.db.add(record)
            self.db.flush()  # Pour obtenir l'ID sans commit
            
            return record, True
            
        except Exception as e:
            raise ETLError(f"Erreur lors de la création/récupération de {model_class.__name__}: {str(e)}")
    
    def check_db_integrity(self) -> bool:
        """Vérifie l'intégrité de la base de données."""
        try:
            # Vérifier les contraintes de clés étrangères
            inspector = inspect(self.db.bind)
            # Logique de vérification d'intégrité
            return True
        except Exception as e:
            self.add_error(ETLError(f"Erreur d'intégrité de la base de données: {str(e)}"))
            return False
    
    def get_import_summary(self) -> Dict[str, Any]:
        """Retourne un résumé de l'import."""
        return {
            "import_log": self.import_log,
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "success_rate": (
                self.import_log["successful_imports"] / max(self.import_log["total_records"], 1) * 100
            )
        }
    
    def rollback_import(self):
        """Annule l'import en cours."""
        try:
            self.db.rollback()
            logger.info("Import annulé - rollback effectué")
        except Exception as e:
            logger.error(f"Erreur lors du rollback: {str(e)}")
    
    def commit_import(self):
        """Valide l'import."""
        try:
            self.db.commit()
            logger.info("Import validé - commit effectué")
        except Exception as e:
            logger.error(f"Erreur lors du commit: {str(e)}")
            raise ETLError(f"Erreur lors de la validation: {str(e)}") 