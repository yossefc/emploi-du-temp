import time
import functools
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta

from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info, Enum,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from prometheus_client.multiprocess import MultiProcessCollector
from fastapi import Request, Response
import psutil

from app.config.environments import settings

# Registre personnalisé pour isoler nos métriques
REGISTRY = CollectorRegistry()

# === MÉTRIQUES HTTP ===

# Compteur de requêtes HTTP
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

# Histogramme du temps de réponse HTTP
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY
)

# Taille des requêtes et réponses
http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    registry=REGISTRY
)

http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    registry=REGISTRY
)

# Requêtes actives
http_requests_active = Gauge(
    'http_requests_active',
    'Number of active HTTP requests',
    registry=REGISTRY
)

# === MÉTRIQUES BASE DE DONNÉES ===

# Compteur de requêtes DB
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'table'],
    registry=REGISTRY
)

# Temps d'exécution des requêtes DB
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
    registry=REGISTRY
)

# Connexions DB actives
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections',
    registry=REGISTRY
)

# Pool de connexions DB
db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size',
    registry=REGISTRY
)

db_connection_pool_checked_out = Gauge(
    'db_connection_pool_checked_out',
    'Database connection pool checked out connections',
    registry=REGISTRY
)

# === MÉTRIQUES BUSINESS ===

# Génération d'emplois du temps
timetable_generations_total = Counter(
    'timetable_generations_total',
    'Total timetable generations',
    ['status'],  # success, failure
    registry=REGISTRY
)

timetable_generation_duration_seconds = Histogram(
    'timetable_generation_duration_seconds',
    'Timetable generation duration in seconds',
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
    registry=REGISTRY
)

# Utilisateurs actifs
active_users = Gauge(
    'active_users_total',
    'Number of active users',
    ['time_window'],  # 1h, 24h, 7d
    registry=REGISTRY
)

# Entités gérées
school_entities = Gauge(
    'school_entities_total',
    'Total number of school entities',
    ['entity_type'],  # subjects, teachers, rooms, classes
    registry=REGISTRY
)

# === MÉTRIQUES SYSTÈME ===

# CPU
system_cpu_usage_percent = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=REGISTRY
)

# Mémoire
system_memory_usage_bytes = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes',
    ['type'],  # total, available, used
    registry=REGISTRY
)

system_memory_usage_percent = Gauge(
    'system_memory_usage_percent',
    'System memory usage percentage',
    registry=REGISTRY
)

# Processus application
process_memory_usage_bytes = Gauge(
    'process_memory_usage_bytes',
    'Process memory usage in bytes',
    registry=REGISTRY
)

process_cpu_usage_percent = Gauge(
    'process_cpu_usage_percent',
    'Process CPU usage percentage',
    registry=REGISTRY
)

# Disque
system_disk_usage_bytes = Gauge(
    'system_disk_usage_bytes',
    'System disk usage in bytes',
    ['type'],  # total, free, used
    registry=REGISTRY
)

system_disk_usage_percent = Gauge(
    'system_disk_usage_percent',
    'System disk usage percentage',
    registry=REGISTRY
)

# === MÉTRIQUES ERREURS ===

# Erreurs d'application
application_errors_total = Counter(
    'application_errors_total',
    'Total application errors',
    ['error_type', 'severity'],
    registry=REGISTRY
)

# Erreurs de validation
validation_errors_total = Counter(
    'validation_errors_total',
    'Total validation errors',
    ['field', 'error_type'],
    registry=REGISTRY
)

# === MÉTRIQUES SÉCURITÉ ===

# Tentatives de connexion
login_attempts_total = Counter(
    'login_attempts_total',
    'Total login attempts',
    ['status'],  # success, failure
    registry=REGISTRY
)

# Accès refusés
access_denied_total = Counter(
    'access_denied_total',
    'Total access denied events',
    ['resource', 'reason'],
    registry=REGISTRY
)

# === INFORMATIONS APPLICATION ===

# Version de l'application
app_info = Info(
    'app_info',
    'Application information',
    registry=REGISTRY
)

# Statut de l'application
app_status = Enum(
    'app_status',
    'Application status',
    states=['starting', 'healthy', 'degraded', 'unhealthy'],
    registry=REGISTRY
)


class MetricsCollector:
    """Collecteur de métriques pour l'application"""
    
    def __init__(self):
        self.start_time = time.time()
        self._update_app_info()
        self._setup_system_metrics_collection()
    
    def _update_app_info(self):
        """Met à jour les informations de l'application"""
        app_info.info({
            'version': settings.APP_VERSION,
            'environment': settings.ENVIRONMENT.value,
            'start_time': datetime.utcnow().isoformat()
        })
    
    def _setup_system_metrics_collection(self):
        """Configure la collecte automatique des métriques système"""
        # Cette méthode sera appelée périodiquement par un scheduler
        pass
    
    def collect_system_metrics(self):
        """Collecte les métriques système actuelles"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage_percent.set(cpu_percent)
            
            # Mémoire système
            memory = psutil.virtual_memory()
            system_memory_usage_bytes.labels(type='total').set(memory.total)
            system_memory_usage_bytes.labels(type='available').set(memory.available)
            system_memory_usage_bytes.labels(type='used').set(memory.used)
            system_memory_usage_percent.set(memory.percent)
            
            # Mémoire processus
            process = psutil.Process()
            process_memory = process.memory_info()
            process_memory_usage_bytes.set(process_memory.rss)
            process_cpu_usage_percent.set(process.cpu_percent())
            
            # Disque
            disk = psutil.disk_usage('/')
            system_disk_usage_bytes.labels(type='total').set(disk.total)
            system_disk_usage_bytes.labels(type='free').set(disk.free)
            system_disk_usage_bytes.labels(type='used').set(disk.used)
            system_disk_usage_percent.set((disk.used / disk.total) * 100)
            
        except Exception as e:
            application_errors_total.labels(
                error_type='metrics_collection',
                severity='warning'
            ).inc()
    
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None
    ):
        """Enregistre une requête HTTP"""
        
        # Compteur total
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        # Durée
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        # Tailles
        if request_size is not None:
            http_request_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)
        
        if response_size is not None:
            http_response_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(response_size)
    
    def record_db_query(
        self,
        operation: str,
        table: str,
        duration: float,
        success: bool = True
    ):
        """Enregistre une requête de base de données"""
        
        db_queries_total.labels(
            operation=operation,
            table=table
        ).inc()
        
        db_query_duration_seconds.labels(
            operation=operation,
            table=table
        ).observe(duration)
        
        if not success:
            application_errors_total.labels(
                error_type='database_query',
                severity='error'
            ).inc()
    
    def record_timetable_generation(
        self,
        success: bool,
        duration: float,
        class_groups_count: int = 0
    ):
        """Enregistre une génération d'emploi du temps"""
        
        status = 'success' if success else 'failure'
        
        timetable_generations_total.labels(status=status).inc()
        timetable_generation_duration_seconds.observe(duration)
        
        if not success:
            application_errors_total.labels(
                error_type='timetable_generation',
                severity='error'
            ).inc()
    
    def record_login_attempt(self, success: bool):
        """Enregistre une tentative de connexion"""
        
        status = 'success' if success else 'failure'
        login_attempts_total.labels(status=status).inc()
    
    def record_access_denied(self, resource: str, reason: str):
        """Enregistre un accès refusé"""
        
        access_denied_total.labels(
            resource=resource,
            reason=reason
        ).inc()
    
    def record_validation_error(self, field: str, error_type: str):
        """Enregistre une erreur de validation"""
        
        validation_errors_total.labels(
            field=field,
            error_type=error_type
        ).inc()
    
    def update_active_users(self, count_1h: int, count_24h: int, count_7d: int):
        """Met à jour le nombre d'utilisateurs actifs"""
        
        active_users.labels(time_window='1h').set(count_1h)
        active_users.labels(time_window='24h').set(count_24h)
        active_users.labels(time_window='7d').set(count_7d)
    
    def update_school_entities(
        self,
        subjects_count: int,
        teachers_count: int,
        rooms_count: int,
        classes_count: int
    ):
        """Met à jour le nombre d'entités scolaires"""
        
        school_entities.labels(entity_type='subjects').set(subjects_count)
        school_entities.labels(entity_type='teachers').set(teachers_count)
        school_entities.labels(entity_type='rooms').set(rooms_count)
        school_entities.labels(entity_type='classes').set(classes_count)
    
    def set_app_status(self, status: str):
        """Définit le statut de l'application"""
        
        app_status.state(status)
    
    def get_uptime_seconds(self) -> float:
        """Retourne l'uptime en secondes"""
        return time.time() - self.start_time


def metrics_middleware(request: Request, call_next: Callable) -> Callable:
    """Middleware pour collecter automatiquement les métriques HTTP"""
    
    async def middleware(request: Request):
        # Incrémenter les requêtes actives
        http_requests_active.inc()
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculer la durée
            duration = time.time() - start_time
            
            # Enregistrer les métriques
            metrics_collector.record_http_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=duration,
                request_size=request.headers.get('content-length'),
                response_size=response.headers.get('content-length')
            )
            
            return response
            
        except Exception as e:
            # Enregistrer l'erreur
            application_errors_total.labels(
                error_type='http_request',
                severity='error'
            ).inc()
            raise
        
        finally:
            # Décrémenter les requêtes actives
            http_requests_active.dec()
    
    return middleware


def get_metrics() -> str:
    """Génère les métriques au format Prometheus"""
    
    # Collecter les métriques système avant de générer
    metrics_collector.collect_system_metrics()
    
    return generate_latest(REGISTRY)


def get_metrics_content_type() -> str:
    """Retourne le content-type pour les métriques Prometheus"""
    return CONTENT_TYPE_LATEST


# Décorateur pour mesurer le temps d'exécution
def measure_time(metric: Histogram, labels: Optional[Dict[str, str]] = None):
    """Décorateur pour mesurer le temps d'exécution d'une fonction"""
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Instance globale du collecteur
metrics_collector = MetricsCollector() 