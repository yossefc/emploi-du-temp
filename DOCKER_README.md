# 🐳 Docker Configuration - School Timetable Generator

Cette documentation explique comment utiliser la configuration Docker complète pour le système de génération d'emplois du temps scolaires.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Pré-requis](#pré-requis)
- [Démarrage rapide](#démarrage-rapide)
- [Configuration des services](#configuration-des-services)
- [Variables d'environnement](#variables-denvironnement)
- [Commandes utiles](#commandes-utiles)
- [Monitoring](#monitoring)
- [Production](#production)
- [Dépannage](#dépannage)

## 🎯 Vue d'ensemble

Cette configuration Docker Compose inclut :

### Services principaux
- **Backend FastAPI** - API REST avec authentification
- **Frontend React** - Interface utilisateur moderne
- **PostgreSQL** - Base de données relationnelle
- **Redis** - Cache et broker pour Celery
- **Nginx** - Reverse proxy et load balancer

### Services de traitement
- **Celery Worker** - Traitement des tâches en arrière-plan
- **Celery Beat** - Planificateur de tâches
- **Flower** - Monitoring Celery

### Outils de développement
- **pgAdmin** - Interface d'administration PostgreSQL
- **Redis Commander** - Interface d'administration Redis

## 🔧 Pré-requis

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB espace disque libre

### Installation Docker sur Windows

```powershell
# Installer Docker Desktop
winget install Docker.DockerDesktop

# Ou télécharger depuis : https://www.docker.com/products/docker-desktop
```

## 🚀 Démarrage rapide

### 1. Cloner et configurer

```bash
# Cloner le projet
git clone <repository-url>
cd school-timetable-generator

# Copier le fichier d'environnement
cp environment.example .env

# Modifier les variables d'environnement
# Éditer .env avec vos valeurs
```

### 2. Lancer l'application

```bash
# Option 1: Script automatisé (Linux/Mac)
./docker-start.sh

# Option 2: Docker Compose direct
docker-compose up -d

# Option 3: Avec outils de développement
docker-compose --profile development up -d
```

### 3. Accéder aux services

Une fois tous les services démarrés :

| Service | URL | Identifiants |
|---------|-----|--------------|
| 🌐 Frontend | http://localhost:3000 | - |
| 🚀 API Backend | http://localhost:8000 | - |
| 📚 Documentation API | http://localhost:8000/docs | - |
| 🌸 Flower (Celery) | http://localhost:5555 | admin / password |
| 🐘 pgAdmin | http://localhost:5050 | admin@school.edu / admin123 |
| 🔴 Redis Commander | http://localhost:8081 | admin / admin123 |

### 4. Connexion application

- **Utilisateur admin** : `admin` / `admin123`
- **Email** : `admin@school.edu`

## ⚙️ Configuration des services

### Backend (FastAPI)

Le backend utilise un Dockerfile multi-stage optimisé :

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim as dependencies
# Installation des dépendances

# Stage 2: Runtime
FROM python:3.11-slim as runtime
# Application optimisée
```

**Caractéristiques** :
- Image Python 3.11 slim
- Utilisateur non-root pour la sécurité
- Health check intégré
- Volumes pour logs et uploads
- Variables d'environnement configurables

### Frontend (React)

Le frontend est servi par Vite en développement :

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  environment:
    REACT_APP_API_URL: http://localhost:8000/api/v1
    CHOKIDAR_USEPOLLING: "true"  # Hot reload
```

### Base de données (PostgreSQL)

Configuration optimisée pour les performances :

```yaml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: school_timetable
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: password
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./backend/scripts/init_db.sql:/docker-entrypoint-initdb.d/01-init.sql:ro
```

**Optimisations incluses** :
- Paramètres PostgreSQL optimisés
- Script d'initialisation automatique
- Données de test pré-chargées
- Health checks

### Cache (Redis)

Redis configuré pour Celery et cache :

```yaml
redis:
  image: redis:7-alpine
  volumes:
    - redis_data:/data
    - ./docker/redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
```

**Configuration** :
- Politique d'éviction LRU
- Limite mémoire configurable
- Optimisations pour Celery
- Persistence RDB

### Reverse Proxy (Nginx)

Nginx configure comme reverse proxy :

```yaml
nginx:
  image: nginx:alpine
  volumes:
    - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./docker/nginx/conf.d:/etc/nginx/conf.d:ro
```

**Fonctionnalités** :
- Load balancing
- Compression gzip
- Headers de sécurité
- Support WebSocket
- Cache statique
- Rate limiting

## 🔐 Variables d'environnement

### Variables essentielles

```bash
# Application
SECRET_KEY=your-super-secret-key-minimum-32-characters
DEBUG=true
ENVIRONMENT=development

# Base de données
POSTGRES_DB=school_timetable
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# IA
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key
USE_CLAUDE=true

# Redis
REDIS_MAXMEMORY=256mb
CELERY_BROKER_URL=redis://redis:6379/1
```

### Variables de sécurité (Production)

```bash
# JWT et authentification
ACCESS_TOKEN_EXPIRE_MINUTES=10080
BCRYPT_ROUNDS=12

# CORS
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]

# SSL
NGINX_HTTPS_PORT=443
```

## 🛠️ Commandes utiles

### Gestion des services

```bash
# Démarrer tous les services
docker-compose up -d

# Démarrer avec profil développement
docker-compose --profile development up -d

# Arrêter tous les services
docker-compose down

# Redémarrer un service spécifique
docker-compose restart backend

# Voir les logs
docker-compose logs -f backend

# Voir le statut
docker-compose ps
```

### Maintenance

```bash
# Mise à jour des images
docker-compose pull

# Reconstruction des services
docker-compose build --no-cache

# Nettoyage
docker-compose down -v  # Supprime aussi les volumes
docker system prune -f  # Nettoie les ressources inutilisées
```

### Base de données

```bash
# Accès direct à PostgreSQL
docker-compose exec postgres psql -U postgres -d school_timetable

# Sauvegarde
docker-compose exec postgres pg_dump -U postgres school_timetable > backup.sql

# Restauration
docker-compose exec -T postgres psql -U postgres -d school_timetable < backup.sql

# Réinitialiser la base
docker-compose down -v
docker-compose up -d postgres
```

### Debugging

```bash
# Accès shell au backend
docker-compose exec backend bash

# Logs détaillés d'un service
docker-compose logs --tail=100 -f backend

# Inspection des variables d'environnement
docker-compose exec backend env

# Tests
docker-compose exec backend pytest

# Performance containers
docker stats
```

## 📊 Monitoring

### Health Checks

Tous les services incluent des health checks :

```bash
# Vérifier l'état de santé
docker-compose ps

# Details d'un service
docker inspect $(docker-compose ps -q backend) | jq '.[].State.Health'
```

### Monitoring avec Flower

Accédez à http://localhost:5555 pour surveiller :
- Tâches Celery en cours
- Workers actifs
- Statistiques de performance
- Historique des tâches

### Logs centralisés

```bash
# Tous les logs
docker-compose logs -f

# Logs spécifiques avec timestamps
docker-compose logs -f -t backend

# Dernières 100 lignes
docker-compose logs --tail=100
```

## 🚀 Production

### Configuration production

1. **Copier le docker-compose.prod.yml** :
```bash
cp docker-compose.prod.yml docker-compose.override.yml
```

2. **Variables d'environnement** :
```bash
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-production-secret-key-very-long-and-secure
DATABASE_URL=postgresql://user:pass@prod-db:5432/dbname
```

3. **SSL/TLS** :
```bash
# Placer vos certificats dans
docker/nginx/ssl/cert.pem
docker/nginx/ssl/key.pem
```

4. **Démarrer** :
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Optimisations production

- Utilisation de Gunicorn au lieu d'Uvicorn
- Plusieurs workers backend
- Cache Nginx activé
- Compression gzip
- Rate limiting strict
- Logs structurés
- Health checks renforcés

## 🔧 Dépannage

### Problèmes courants

**Port déjà utilisé** :
```bash
# Trouver le processus utilisant le port
netstat -tulpn | grep :8000
# Modifier le port dans .env
BACKEND_PORT=8001
```

**Services qui ne démarrent pas** :
```bash
# Vérifier les logs
docker-compose logs service-name

# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -h
```

**Base de données corrompue** :
```bash
# Supprimer et recréer
docker-compose down -v
docker volume rm emploi-du-temp_postgres_data
docker-compose up -d
```

**Permission denied sur volumes** :
```bash
# Fixer les permissions
sudo chown -R $USER:$USER backend/logs backend/uploads
```

### Performance

**Optimisation mémoire** :
```bash
# Ajuster dans .env
REDIS_MAXMEMORY=512mb
GUNICORN_WORKERS=2
```

**Monitoring ressources** :
```bash
# Utilisation en temps réel
docker stats

# Logs de performance
docker-compose logs nginx | grep "request_time"
```

### Support

Pour obtenir de l'aide :

1. Vérifiez les logs : `docker-compose logs`
2. Consultez la documentation API : http://localhost:8000/docs
3. Vérifiez les variables d'environnement
4. Testez les connexions réseau entre services

## 📚 Ressources additionnelles

- [Documentation Docker Compose](https://docs.docker.com/compose/)
- [Guide FastAPI](https://fastapi.tiangolo.com/)
- [Configuration Nginx](https://nginx.org/en/docs/)
- [Redis Configuration](https://redis.io/topics/config)
- [PostgreSQL Tuning](https://www.postgresql.org/docs/current/runtime-config.html)

---

**Note** : Cette configuration est optimisée pour le développement local. Pour la production, assurez-vous de réviser toutes les variables de sécurité et les configurations réseau. 