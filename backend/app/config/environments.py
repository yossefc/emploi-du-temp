import os
import secrets
from typing import Optional, Dict, Any, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class BaseConfig(BaseSettings):
    """Configuration de base commune à tous les environnements"""
    
    # Application
    APP_NAME: str = "École Emploi du Temps"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    
    # Base de données
    DATABASE_URL: str = Field(default="sqlite:///./school_timetable.db")
    DATABASE_POOL_SIZE: int = Field(default=5, ge=1, le=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=30)
    
    # Sécurité
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    DOCS_URL: Optional[str] = "/docs"
    REDOC_URL: Optional[str] = "/redoc"
    OPENAPI_URL: Optional[str] = "/openapi.json"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # secondes
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json ou text
    LOG_FILE: Optional[str] = None
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    
    # Feature Flags
    FEATURE_TIMETABLE_AI: bool = True
    FEATURE_ADVANCED_ANALYTICS: bool = True
    FEATURE_MOBILE_PUSH: bool = False
    FEATURE_EXPORT_PDF: bool = True
    FEATURE_BACKUP_AUTO: bool = True
    
    # Monitoring
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_ENDPOINT: str = "/health"
    PROMETHEUS_METRICS_PATH: str = "/metrics"
    
    # Cache
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 300  # 5 minutes
    
    # Email (pour notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".xlsx", ".csv", ".json"]
    
    # Backup
    BACKUP_DIR: str = "backups"
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_SCHEDULE: str = "0 2 * * *"  # Cron: tous les jours à 2h
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL ne peut pas être vide")
        return v
    
    @validator("SECRET_KEY", "JWT_SECRET_KEY")
    def validate_secret_keys(cls, v):
        if len(v) < 32:
            raise ValueError("Les clés secrètes doivent faire au moins 32 caractères")
        return v


class DevelopmentConfig(BaseConfig):
    """Configuration pour l'environnement de développement"""
    
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # Base de données locale
    DATABASE_URL: str = "sqlite:///./school_timetable_dev.db"
    
    # Rate limiting plus permissif
    RATE_LIMIT_REQUESTS: int = 1000
    
    # Features activées pour les tests
    FEATURE_TIMETABLE_AI: bool = True
    FEATURE_ADVANCED_ANALYTICS: bool = True
    FEATURE_MOBILE_PUSH: bool = True
    FEATURE_EXPORT_PDF: bool = True
    FEATURE_BACKUP_AUTO: bool = False  # Pas de backup auto en dev
    
    # CORS permissif pour le développement
    CORS_ORIGINS: List[str] = ["*"]


class StagingConfig(BaseConfig):
    """Configuration pour l'environnement de staging"""
    
    ENVIRONMENT: Environment = Environment.STAGING
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Base de données staging
    DATABASE_URL: str = Field(..., env="STAGING_DATABASE_URL")
    
    # Rate limiting modéré
    RATE_LIMIT_REQUESTS: int = 500
    
    # Certaines features peuvent être testées
    FEATURE_MOBILE_PUSH: bool = False  # Pas de notifications en staging
    FEATURE_BACKUP_AUTO: bool = True
    
    # Docs disponibles mais protégées
    DOCS_URL: str = "/staging-docs"
    REDOC_URL: str = "/staging-redoc"
    
    # CORS restreint aux domaines de staging
    CORS_ORIGINS: List[str] = [
        "https://staging-school-timetable.example.com",
        "http://localhost:3000"
    ]


class ProductionConfig(BaseConfig):
    """Configuration pour l'environnement de production"""
    
    ENVIRONMENT: Environment = Environment.PRODUCTION
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    
    # Base de données production (obligatoire)
    DATABASE_URL: str = Field(..., env="PRODUCTION_DATABASE_URL")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Sécurité renforcée
    SECRET_KEY: str = Field(..., env="PRODUCTION_SECRET_KEY")
    JWT_SECRET_KEY: str = Field(..., env="PRODUCTION_JWT_SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Plus court en prod
    
    # Rate limiting strict
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW: int = 60
    
    # Features production
    FEATURE_MOBILE_PUSH: bool = True
    FEATURE_BACKUP_AUTO: bool = True
    
    # Pas de documentation publique en production
    DOCS_URL: Optional[str] = None
    REDOC_URL: Optional[str] = None
    OPENAPI_URL: Optional[str] = None
    
    # CORS strict
    CORS_ORIGINS: List[str] = Field(..., env="PRODUCTION_CORS_ORIGINS")
    
    # Logging en fichier obligatoire
    LOG_FILE: str = Field(default="/var/log/school-timetable/app.log")
    
    # Cache Redis obligatoire
    REDIS_URL: str = Field(..., env="PRODUCTION_REDIS_URL")
    
    # Email obligatoire pour les notifications
    SMTP_HOST: str = Field(..., env="PRODUCTION_SMTP_HOST")
    SMTP_USERNAME: str = Field(..., env="PRODUCTION_SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(..., env="PRODUCTION_SMTP_PASSWORD")


def get_config() -> BaseConfig:
    """Factory pour obtenir la configuration selon l'environnement"""
    
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    config_mapping = {
        "development": DevelopmentConfig,
        "staging": StagingConfig,
        "production": ProductionConfig
    }
    
    config_class = config_mapping.get(env, DevelopmentConfig)
    return config_class()


def get_feature_flags() -> Dict[str, bool]:
    """Récupère tous les feature flags actifs"""
    
    config = get_config()
    
    return {
        "timetable_ai": config.FEATURE_TIMETABLE_AI,
        "advanced_analytics": config.FEATURE_ADVANCED_ANALYTICS,
        "mobile_push": config.FEATURE_MOBILE_PUSH,
        "export_pdf": config.FEATURE_EXPORT_PDF,
        "backup_auto": config.FEATURE_BACKUP_AUTO,
    }


def is_feature_enabled(feature_name: str) -> bool:
    """Vérifie si une feature est activée"""
    
    flags = get_feature_flags()
    return flags.get(feature_name, False)


# Instance globale de configuration
settings = get_config() 