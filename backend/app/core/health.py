import asyncio
import time
import psutil
import redis
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
import aiohttp
import logging

from app.config.environments import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)


class HealthStatus:
    """Statuts de santé possible"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class HealthCheck:
    """Classe de base pour les vérifications de santé"""
    
    def __init__(self, name: str, timeout: int = 10):
        self.name = name
        self.timeout = timeout
        self.last_check = None
        self.status = HealthStatus.UNKNOWN
        self.details = {}
    
    async def check(self) -> Dict[str, Any]:
        """Effectue la vérification de santé"""
        start_time = time.time()
        
        try:
            # Implémentation spécifique dans les sous-classes
            result = await self._perform_check()
            
            self.status = HealthStatus.HEALTHY
            self.details = result
            
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {str(e)}")
            self.status = HealthStatus.UNHEALTHY
            self.details = {"error": str(e)}
        
        finally:
            self.last_check = datetime.utcnow()
            response_time = (time.time() - start_time) * 1000  # en ms
            
            return {
                "name": self.name,
                "status": self.status,
                "timestamp": self.last_check.isoformat(),
                "response_time_ms": round(response_time, 2),
                "details": self.details
            }
    
    async def _perform_check(self) -> Dict[str, Any]:
        """À implémenter dans les sous-classes"""
        raise NotImplementedError


class DatabaseHealthCheck(HealthCheck):
    """Vérification de santé de la base de données"""
    
    def __init__(self):
        super().__init__("database", timeout=5)
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Vérifie la connectivité et les performances de la base de données"""
        
        try:
            # Test de connectivité
            async for db in get_db():
                # Test simple de connexion
                result = await db.execute(text("SELECT 1"))
                connection_ok = result.scalar() == 1
                
                if not connection_ok:
                    raise Exception("Database connection test failed")
                
                # Test de performance avec une requête plus complexe
                start_time = time.time()
                await db.execute(text("SELECT COUNT(*) FROM subjects"))
                query_time = (time.time() - start_time) * 1000
                
                # Informations sur la base de données
                db_info = await db.execute(text("PRAGMA database_list"))
                db_list = db_info.fetchall()
                
                return {
                    "connection": "ok",
                    "query_time_ms": round(query_time, 2),
                    "database_count": len(db_list),
                    "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "local"
                }
                
        except Exception as e:
            raise Exception(f"Database health check failed: {str(e)}")


class RedisHealthCheck(HealthCheck):
    """Vérification de santé de Redis (si configuré)"""
    
    def __init__(self):
        super().__init__("redis", timeout=3)
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Vérifie la connectivité Redis"""
        
        if not settings.REDIS_URL:
            return {"status": "not_configured"}
        
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            
            # Test de ping
            start_time = time.time()
            pong = redis_client.ping()
            ping_time = (time.time() - start_time) * 1000
            
            if not pong:
                raise Exception("Redis ping failed")
            
            # Informations Redis
            info = redis_client.info()
            
            return {
                "ping": "pong",
                "ping_time_ms": round(ping_time, 2),
                "version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown")
            }
            
        except Exception as e:
            raise Exception(f"Redis health check failed: {str(e)}")


class SystemHealthCheck(HealthCheck):
    """Vérification de santé du système"""
    
    def __init__(self):
        super().__init__("system", timeout=2)
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Vérifie les ressources système"""
        
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Mémoire
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disque
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024**3)
            
            # Processus
            process = psutil.Process()
            process_memory_mb = process.memory_info().rss / (1024**2)
            process_cpu_percent = process.cpu_percent()
            
            # Déterminer le statut
            status = "healthy"
            alerts = []
            
            if cpu_percent > 80:
                status = "degraded"
                alerts.append("High CPU usage")
            
            if memory_percent > 85:
                status = "degraded"
                alerts.append("High memory usage")
            
            if disk_percent > 90:
                status = "unhealthy"
                alerts.append("Low disk space")
            
            return {
                "status": status,
                "alerts": alerts,
                "cpu": {
                    "usage_percent": round(cpu_percent, 1),
                    "count": cpu_count
                },
                "memory": {
                    "usage_percent": round(memory_percent, 1),
                    "available_gb": round(memory_available_gb, 2)
                },
                "disk": {
                    "usage_percent": round(disk_percent, 1),
                    "free_gb": round(disk_free_gb, 2)
                },
                "process": {
                    "memory_mb": round(process_memory_mb, 2),
                    "cpu_percent": round(process_cpu_percent, 1)
                }
            }
            
        except Exception as e:
            raise Exception(f"System health check failed: {str(e)}")


class ExternalServiceHealthCheck(HealthCheck):
    """Vérification de santé des services externes"""
    
    def __init__(self, service_name: str, url: str, timeout: int = 5):
        super().__init__(f"external_{service_name}", timeout)
        self.service_name = service_name
        self.url = url
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Vérifie la disponibilité d'un service externe"""
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                start_time = time.time()
                async with session.get(self.url) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    return {
                        "service": self.service_name,
                        "url": self.url,
                        "status_code": response.status,
                        "response_time_ms": round(response_time, 2),
                        "available": response.status < 400
                    }
                    
        except Exception as e:
            raise Exception(f"External service {self.service_name} health check failed: {str(e)}")


class HealthManager:
    """Gestionnaire principal des vérifications de santé"""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.startup_time = datetime.utcnow()
        self._setup_checks()
    
    def _setup_checks(self):
        """Configure les vérifications de santé"""
        
        # Vérifications de base toujours activées
        self.checks.extend([
            DatabaseHealthCheck(),
            SystemHealthCheck()
        ])
        
        # Redis si configuré
        if settings.REDIS_URL:
            self.checks.append(RedisHealthCheck())
        
        # Services externes si en production
        if settings.ENVIRONMENT.value == "production":
            # Ajouter ici les vérifications de services externes
            pass
    
    async def check_all(self, include_details: bool = True) -> Dict[str, Any]:
        """Effectue toutes les vérifications de santé"""
        
        start_time = time.time()
        
        # Exécuter toutes les vérifications en parallèle
        tasks = [check.check() for check in self.checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyser les résultats
        healthy_count = 0
        unhealthy_count = 0
        degraded_count = 0
        check_details = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                unhealthy_count += 1
                check_details.append({
                    "name": self.checks[i].name,
                    "status": HealthStatus.UNHEALTHY,
                    "error": str(result)
                })
            else:
                if result["status"] == HealthStatus.HEALTHY:
                    healthy_count += 1
                elif result["status"] == HealthStatus.UNHEALTHY:
                    unhealthy_count += 1
                elif result["status"] == HealthStatus.DEGRADED:
                    degraded_count += 1
                
                if include_details:
                    check_details.append(result)
                else:
                    check_details.append({
                        "name": result["name"],
                        "status": result["status"]
                    })
        
        # Déterminer le statut global
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        total_time = (time.time() - start_time) * 1000
        uptime = datetime.utcnow() - self.startup_time
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT.value,
            "checks": {
                "total": len(self.checks),
                "healthy": healthy_count,
                "unhealthy": unhealthy_count,
                "degraded": degraded_count
            },
            "response_time_ms": round(total_time, 2),
            "details": check_details if include_details else None
        }
    
    async def check_readiness(self) -> bool:
        """Vérifie si l'application est prête à recevoir du trafic"""
        
        result = await self.check_all(include_details=False)
        return result["status"] in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    
    async def check_liveness(self) -> bool:
        """Vérifie si l'application est vivante (pour les restart automatiques)"""
        
        try:
            # Test très basique - si on peut exécuter cette fonction, on est vivant
            database_check = DatabaseHealthCheck()
            result = await database_check.check()
            return result["status"] != HealthStatus.UNHEALTHY
            
        except Exception:
            return False


# Instance globale
health_manager = HealthManager() 