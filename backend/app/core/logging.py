import logging
import logging.handlers
import json
import time
import traceback
import uuid
from typing import Any, Dict, Optional
from datetime import datetime
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from pythonjsonlogger import jsonlogger
from fastapi import Request, Response
import structlog

from app.config.environments import settings

# Context variable pour le correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class CorrelationIDFilter(logging.Filter):
    """Filtre pour ajouter le correlation ID aux logs"""
    
    def filter(self, record):
        record.correlation_id = correlation_id.get() or "no-correlation-id"
        return True


class JsonFormatter(jsonlogger.JsonFormatter):
    """Formateur JSON personnalisé pour les logs structurés"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s %(name)s %(levelname)s %(correlation_id)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Ajouter des champs standards
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['environment'] = settings.ENVIRONMENT.value
        log_record['version'] = settings.APP_VERSION
        
        # Ajouter le correlation ID
        log_record['correlation_id'] = getattr(record, 'correlation_id', None)
        
        # Ajouter l'exception si présente
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Ajouter des métadonnées spécifiques si présentes
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        if hasattr(record, 'endpoint'):
            log_record['endpoint'] = record.endpoint
        
        if hasattr(record, 'method'):
            log_record['method'] = record.method
        
        if hasattr(record, 'status_code'):
            log_record['status_code'] = record.status_code
        
        if hasattr(record, 'response_time'):
            log_record['response_time_ms'] = record.response_time


class TextFormatter(logging.Formatter):
    """Formateur texte pour le développement"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(correlation_id)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class RequestLoggerMixin:
    """Mixin pour ajouter des informations de requête aux logs"""
    
    @staticmethod
    def log_request(
        logger: logging.Logger,
        request: Request,
        response: Response,
        response_time: float,
        **kwargs
    ):
        """Log une requête HTTP avec tous les détails"""
        
        extra = {
            'method': request.method,
            'endpoint': str(request.url.path),
            'query_params': dict(request.query_params),
            'status_code': response.status_code,
            'response_time': round(response_time * 1000, 2),  # en ms
            'user_agent': request.headers.get('user-agent'),
            'client_ip': request.client.host if request.client else None,
            **kwargs
        }
        
        # Log selon le niveau approprié
        if response.status_code >= 500:
            logger.error(f"HTTP {request.method} {request.url.path}", extra=extra)
        elif response.status_code >= 400:
            logger.warning(f"HTTP {request.method} {request.url.path}", extra=extra)
        else:
            logger.info(f"HTTP {request.method} {request.url.path}", extra=extra)


class SecurityLogger:
    """Logger spécialisé pour les événements de sécurité"""
    
    def __init__(self):
        self.logger = logging.getLogger("security")
    
    def log_login_attempt(self, username: str, success: bool, ip: str, user_agent: str):
        """Log une tentative de connexion"""
        
        extra = {
            'event_type': 'login_attempt',
            'username': username,
            'success': success,
            'client_ip': ip,
            'user_agent': user_agent
        }
        
        if success:
            self.logger.info(f"Successful login for user {username}", extra=extra)
        else:
            self.logger.warning(f"Failed login attempt for user {username}", extra=extra)
    
    def log_permission_denied(self, user_id: int, resource: str, action: str):
        """Log un refus d'accès"""
        
        extra = {
            'event_type': 'permission_denied',
            'user_id': user_id,
            'resource': resource,
            'action': action
        }
        
        self.logger.warning(f"Permission denied for user {user_id} on {resource}:{action}", extra=extra)
    
    def log_suspicious_activity(self, description: str, details: Dict[str, Any]):
        """Log une activité suspecte"""
        
        extra = {
            'event_type': 'suspicious_activity',
            'description': description,
            **details
        }
        
        self.logger.error(f"Suspicious activity detected: {description}", extra=extra)


class PerformanceLogger:
    """Logger spécialisé pour les métriques de performance"""
    
    def __init__(self):
        self.logger = logging.getLogger("performance")
    
    def log_slow_query(self, query: str, duration: float, params: Optional[Dict] = None):
        """Log une requête lente"""
        
        extra = {
            'event_type': 'slow_query',
            'query': query,
            'duration_ms': round(duration * 1000, 2),
            'params': params
        }
        
        self.logger.warning(f"Slow query detected ({duration:.3f}s)", extra=extra)
    
    def log_endpoint_performance(self, endpoint: str, method: str, duration: float, status_code: int):
        """Log les performances d'un endpoint"""
        
        extra = {
            'event_type': 'endpoint_performance',
            'endpoint': endpoint,
            'method': method,
            'duration_ms': round(duration * 1000, 2),
            'status_code': status_code
        }
        
        # Log selon la durée
        if duration > 5.0:  # Plus de 5 secondes
            self.logger.error(f"Very slow endpoint {method} {endpoint}", extra=extra)
        elif duration > 1.0:  # Plus de 1 seconde
            self.logger.warning(f"Slow endpoint {method} {endpoint}", extra=extra)
        else:
            self.logger.info(f"Endpoint performance {method} {endpoint}", extra=extra)


class BusinessLogger:
    """Logger spécialisé pour les événements métier"""
    
    def __init__(self):
        self.logger = logging.getLogger("business")
    
    def log_timetable_generation(self, user_id: int, class_groups: list, duration: float, success: bool):
        """Log la génération d'un emploi du temps"""
        
        extra = {
            'event_type': 'timetable_generation',
            'user_id': user_id,
            'class_groups_count': len(class_groups),
            'class_groups': class_groups,
            'duration_ms': round(duration * 1000, 2),
            'success': success
        }
        
        if success:
            self.logger.info(f"Timetable generated successfully for {len(class_groups)} groups", extra=extra)
        else:
            self.logger.error(f"Timetable generation failed for {len(class_groups)} groups", extra=extra)
    
    def log_data_import(self, user_id: int, import_type: str, records_count: int, success: bool):
        """Log un import de données"""
        
        extra = {
            'event_type': 'data_import',
            'user_id': user_id,
            'import_type': import_type,
            'records_count': records_count,
            'success': success
        }
        
        if success:
            self.logger.info(f"Data import successful: {records_count} {import_type} records", extra=extra)
        else:
            self.logger.error(f"Data import failed for {import_type}", extra=extra)


def setup_logging():
    """Configure le système de logging"""
    
    # Créer le répertoire de logs si nécessaire
    if settings.LOG_FILE:
        log_dir = Path(settings.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuration du logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Supprimer les handlers existants
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Formatter selon l'environnement
    if settings.LOG_FORMAT == "json":
        formatter = JsonFormatter()
    else:
        formatter = TextFormatter()
    
    # Handler console (toujours présent)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(CorrelationIDFilter())
    root_logger.addHandler(console_handler)
    
    # Handler fichier (si configuré)
    if settings.LOG_FILE:
        # Handler avec rotation
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=settings.LOG_FILE,
            when='midnight',
            interval=1,
            backupCount=int(settings.LOG_RETENTION.split()[0]),
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(CorrelationIDFilter())
        root_logger.addHandler(file_handler)
    
    # Configuration des loggers externes
    logging.getLogger("uvicorn.access").disabled = True  # On gère nous-mêmes les logs d'accès
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # Réduire les logs SQL
    
    # Logger spécialisés
    for logger_name in ["security", "performance", "business"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)


@contextmanager
def request_correlation_id(request_id: Optional[str] = None):
    """Context manager pour gérer le correlation ID d'une requête"""
    
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    token = correlation_id.set(request_id)
    try:
        yield request_id
    finally:
        correlation_id.reset(token)


def get_correlation_id() -> Optional[str]:
    """Récupère le correlation ID actuel"""
    return correlation_id.get()


def set_correlation_id(request_id: str):
    """Définit le correlation ID"""
    correlation_id.set(request_id)


# Instances globales des loggers spécialisés
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()
business_logger = BusinessLogger()


# Configuration automatique
setup_logging() 