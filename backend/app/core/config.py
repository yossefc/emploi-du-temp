"""
Configuration settings for the School Timetable Generator application.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "School Timetable Generator"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/school_timetable"
    )
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    
    # AI settings
    USE_CLAUDE: bool = os.getenv("USE_CLAUDE", "true").lower() == "true"
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    AI_MODEL: str = os.getenv("AI_MODEL", "claude-3-opus-20240229")  # or "gpt-4"
    AI_TEMPERATURE: float = 0.3
    AI_MAX_TOKENS: int = 4000
    
    # Solver settings
    SOLVER_TIME_LIMIT_SECONDS: int = 300  # 5 minutes max
    SOLVER_NUM_WORKERS: int = 8  # Number of parallel workers for CP-SAT
    
    # Israeli-specific settings
    FRIDAY_SHORT_DAY: bool = True
    FRIDAY_END_HOUR: int = 13  # 1 PM
    REGULAR_END_HOUR: int = 16  # 4 PM
    START_HOUR: int = 8  # 8 AM
    LESSON_DURATION_MINUTES: int = 45
    BREAK_DURATION_MINUTES: int = 10
    
    # Language settings
    DEFAULT_LANGUAGE: str = "he"  # Hebrew by default
    SUPPORTED_LANGUAGES: List[str] = ["he", "fr"]
    
    # File upload settings
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    """
    return Settings()


settings = get_settings() 