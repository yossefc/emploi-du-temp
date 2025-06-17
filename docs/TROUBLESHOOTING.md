# 🔧 Guide de Dépannage - École Emploi du Temps

Ce guide vous aidera à diagnostiquer et résoudre les problèmes les plus couramment rencontrés avec l'application École Emploi du Temps.

## 📋 Table des Matières

- [Diagnostic Rapide](#diagnostic-rapide)
- [Problèmes d'Installation](#problèmes-dinstallation)
- [Problèmes de Connexion](#problèmes-de-connexion)
- [Problèmes Base de Données](#problèmes-base-de-données)
- [Problèmes de Performance](#problèmes-de-performance)
- [Problèmes de Génération](#problèmes-de-génération)
- [Problèmes Frontend](#problèmes-frontend)
- [Problèmes de Monitoring](#problèmes-de-monitoring)
- [Collecte d'Informations](#collecte-dinformations)
- [Escalade Support](#escalade-support)

## 🩺 Diagnostic Rapide

### Checklist Première Intervention

Avant de creuser plus profondément, vérifiez ces points essentiels :

```bash
# 1. Services running
docker-compose ps

# 2. Health checks
curl -f http://localhost:8000/health
curl -f http://localhost:3000/health

# 3. Logs récents
docker-compose logs --tail=50 app
docker-compose logs --tail=50 frontend

# 4. Ressources système
docker stats
df -h
free -m
```

### Statuts de Service

| Service | Port | Health Check | Status Attendu |
|---------|------|--------------|----------------|
| Frontend | 3000 | `/health` | `healthy` |
| Backend | 8000 | `/health` | `healthy` |
| PostgreSQL | 5432 | `pg_isready` | `accepting connections` |
| Redis | 6379 | `ping` | `PONG` |

### Codes d'Erreur Courants

| Code | Signification | Action Immédiate |
|------|---------------|------------------|
| **500** | Erreur serveur interne | Vérifier logs backend |
| **502** | Bad Gateway | Vérifier services backend |
| **503** | Service indisponible | Vérifier santé services |
| **404** | Ressource introuvable | Vérifier routes/configuration |
| **401** | Non autorisé | Vérifier authentification |
| **403** | Accès refusé | Vérifier permissions |

## 🚀 Problèmes d'Installation

### Docker et Docker Compose

#### Problème : Docker non installé ou obsolète

**Symptômes :**
```
docker: command not found
```

**Solution :**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Redémarrer session
exit
# Se reconnecter

# Vérifier installation
docker version
docker-compose version
```

#### Problème : Permissions Docker refusées

**Symptômes :**
```
Got permission denied while trying to connect to the Docker daemon socket
```

**Solution :**
```bash
# Ajouter utilisateur au groupe docker
sudo usermod -aG docker $USER

# Redémarrer session ou
newgrp docker

# Vérifier
docker ps
```

#### Problème : Version Docker Compose incompatible

**Symptômes :**
```
ERROR: Version in "./docker-compose.yml" is unsupported
```

**Solution :**
```bash
# Mettre à jour Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Vérifier version
docker-compose version
```

### Problèmes de Build

#### Problème : Build échoue sur les dépendances

**Symptômes :**
```
ERROR: Could not find a version that satisfies the requirement
```

**Solution :**
```bash
# Nettoyer le cache Docker
docker system prune -f
docker builder prune -f

# Rebuild from scratch
docker-compose build --no-cache --parallel

# Si problème persistant, vérifier requirements.txt
cd backend
pip install -r requirements.txt
```

#### Problème : Erreur de téléchargement d'images

**Symptômes :**
```
Error response from daemon: pull access denied
```

**Solution :**
```bash
# Vérifier connexion internet
ping 8.8.8.8

# Nettoyer images corrompues
docker image prune -f

# Télécharger manuellement
docker pull postgres:15
docker pull redis:7
docker pull node:18-alpine
```

## 🔐 Problèmes de Connexion

### Authentification

#### Problème : Impossible de se connecter

**Symptômes :**
- Message "Invalid credentials"
- Page de connexion en boucle
- Erreur 401

**Diagnostic :**
```bash
# Vérifier les utilisateurs en base
docker-compose exec app python -c "
from app.models.user import User
from app.core.database import get_db
for db in get_db():
    users = db.query(User).all()
    for user in users:
        print(f'{user.email} - Active: {user.is_active}')
    break
"
```

**Solutions :**

1. **Créer un utilisateur admin :**
```bash
docker-compose exec app python create_test_user.py
```

2. **Réinitialiser mot de passe :**
```bash
docker-compose exec app python -c "
from app.models.user import User
from app.core.database import get_db
from app.core.security import get_password_hash

for db in get_db():
    user = db.query(User).filter(User.email == 'admin@example.com').first()
    if user:
        user.hashed_password = get_password_hash('newpassword123')
        db.commit()
        print('Password reset successfully')
    break
"
```

#### Problème : Tokens JWT expirés

**Symptômes :**
- Déconnexion fréquente
- Erreur "Token expired"

**Solution :**
```bash
# Vérifier configuration JWT
docker-compose exec app python -c "
from app.config.environments import settings
print(f'Access token expires in: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes')
print(f'JWT Secret length: {len(settings.JWT_SECRET_KEY)}')
"

# Ajuster dans .env si nécessaire
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Problèmes CORS

#### Problème : Frontend ne peut pas appeler l'API

**Symptômes :**
- Erreurs CORS dans la console navigateur
- "Access to fetch blocked by CORS policy"

**Solution :**
```bash
# Vérifier configuration CORS
docker-compose exec app python -c "
from app.config.environments import settings
print(f'CORS Origins: {settings.CORS_ORIGINS}')
"

# Ajuster dans .env
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
```

## 🗄️ Problèmes Base de Données

### PostgreSQL

#### Problème : Base de données inaccessible

**Symptômes :**
```
psql: could not connect to server: Connection refused
```

**Diagnostic :**
```bash
# Vérifier status PostgreSQL
docker-compose exec postgres pg_isready -U school_user

# Vérifier logs
docker-compose logs postgres

# Vérifier variables d'environnement
docker-compose exec postgres env | grep POSTGRES
```

**Solutions :**

1. **Redémarrer PostgreSQL :**
```bash
docker-compose restart postgres
sleep 10
docker-compose exec postgres pg_isready -U school_user
```

2. **Vérifier/Recréer la base :**
```bash
# Se connecter à PostgreSQL
docker-compose exec postgres psql -U school_user -d school_timetable

# Dans psql :
\l                          -- Lister bases
\dt                         -- Lister tables
SELECT version();           -- Version PostgreSQL
\q                          -- Quitter
```

#### Problème : Erreurs de migration

**Symptômes :**
```
sqlalchemy.exc.ProgrammingError: relation "subjects" does not exist
```

**Solution :**
```bash
# Vérifier status migrations
docker-compose exec app alembic current
docker-compose exec app alembic history

# Appliquer migrations
docker-compose exec app alembic upgrade head

# Si échec, réinitialiser
docker-compose exec app alembic downgrade base
docker-compose exec app alembic upgrade head
```

### SQLite (Développement)

#### Problème : Base de données corrompue

**Symptômes :**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solution :**
```bash
# Sauvegarder données si possible
cp backend/school_timetable.db backend/school_timetable.db.backup

# Recréer base de données
rm backend/school_timetable.db
docker-compose exec app alembic upgrade head

# Recharger données de test
docker-compose exec app python scripts/load_test_data.py
```

### Problèmes de Performance Base

#### Problème : Requêtes lentes

**Diagnostic :**
```sql
-- Dans PostgreSQL
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;

-- Analyser une requête spécifique
EXPLAIN ANALYZE SELECT * FROM subjects WHERE niveau_requis = 9;
```

**Solutions :**
```sql
-- Créer indexes manquants
CREATE INDEX idx_subjects_niveau ON subjects(niveau_requis);
CREATE INDEX idx_classes_niveau ON classes(niveau);

-- Nettoyer statistiques
ANALYZE;
VACUUM ANALYZE;
```

## ⚡ Problèmes de Performance

### Lenteur Générale

#### Diagnostic Ressources

```bash
# CPU et mémoire
htop
# ou
docker stats

# Espace disque
df -h

# I/O disque
iotop

# Réseau
netstat -i
```

#### Problème : Mémoire insuffisante

**Symptômes :**
- Services qui redémarrent (OOMKilled)
- Lenteur extrême
- Swap élevé

**Solution :**
```bash
# Vérifier utilisation mémoire
free -h
docker stats --no-stream

# Ajuster limites dans docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

# Ajouter swap si nécessaire
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### Problème : CPU élevé

**Solution :**
```bash
# Identifier processus gourmands
docker exec -it $(docker-compose ps -q app) top

# Vérifier logs pour boucles infinies
docker-compose logs app | grep -i "error\|timeout\|exception"

# Redimensionner si nécessaire
docker-compose up -d --scale app=2
```

### Performance Base de Données

#### Optimisation PostgreSQL

```bash
# Configurer PostgreSQL pour de meilleures performances
docker-compose exec postgres psql -U school_user -d school_timetable -c "
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
"

# Analyser performances
docker-compose exec postgres psql -U school_user -d school_timetable -c "
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public';
"
```

### Cache Redis

#### Problème : Cache non fonctionnel

**Diagnostic :**
```bash
# Tester connexion Redis
docker-compose exec redis redis-cli ping

# Vérifier utilisation
docker-compose exec redis redis-cli info memory

# Lister clés
docker-compose exec redis redis-cli keys "*"
```

**Solution :**
```bash
# Nettoyer cache si corrompu
docker-compose exec redis redis-cli flushall

# Redémarrer Redis
docker-compose restart redis
```

## 🧮 Problèmes de Génération

### Échecs de Génération

#### Problème : Génération échoue systématiquement

**Symptômes :**
- Message "No solution found"
- Timeout de génération
- Erreurs de contraintes

**Diagnostic :**
```bash
# Vérifier logs détaillés
docker-compose logs app | grep -i "generation\|solver\|constraint"

# Vérifier données d'entrée
docker-compose exec app python -c "
from app.models.subject import Subject
from app.models.classroom import ClassRoom
from app.models.teacher import Teacher
from app.core.database import get_db

for db in get_db():
    subjects_count = db.query(Subject).count()
    rooms_count = db.query(ClassRoom).count()
    teachers_count = db.query(Teacher).count()
    
    print(f'Subjects: {subjects_count}')
    print(f'Rooms: {rooms_count}')  
    print(f'Teachers: {teachers_count}')
    break
"
```

**Solutions :**

1. **Vérifier cohérence des données :**
```bash
# Script de validation
docker-compose exec app python -c "
from app.services.validation import validate_timetable_data
result = validate_timetable_data()
for error in result.errors:
    print(f'ERROR: {error}')
for warning in result.warnings:
    print(f'WARNING: {warning}')
"
```

2. **Réduire la complexité :**
```bash
# Commencer avec moins de classes
# Réduire les contraintes non essentielles
# Augmenter la flexibilité des horaires
```

#### Problème : Génération très lente

**Solutions :**
```bash
# Ajuster paramètres solveur
export SOLVER_TIMEOUT=300  # 5 minutes max
export SOLVER_WORKERS=4    # Parallélisme

# Optimiser algorithme
export USE_HEURISTICS=true
export CONSTRAINT_PRIORITY=high
```

### Qualité des Résultats

#### Problème : Résultats non optimaux

**Diagnostic :**
```bash
# Analyser qualité du résultat
docker-compose exec app python -c "
from app.services.timetable_analyzer import analyze_timetable
results = analyze_timetable(timetable_id=1)
print(f'Quality Score: {results.quality_score}%')
print(f'Conflicts: {len(results.conflicts)}')
print(f'Preferences Satisfied: {results.preferences_satisfied}%')
"
```

## 🌐 Problèmes Frontend

### Erreurs React

#### Problème : Page blanche après build

**Diagnostic :**
```bash
# Vérifier console navigateur (F12)
# Chercher erreurs JavaScript

# Vérifier build
cd frontend
npm run build

# Tester en local
npx serve -s build -l 3000
```

**Solutions :**
```bash
# Nettoyer cache
rm -rf frontend/node_modules frontend/.next frontend/build
cd frontend
npm install
npm run build

# Vérifier variables d'environnement
echo $REACT_APP_API_URL
```

#### Problème : Composants ne se chargent pas

**Solution :**
```bash
# Vérifier imports
grep -r "import.*from" frontend/src/ | grep -v node_modules

# Vérifier TypeScript
cd frontend
npm run type-check

# Rebuild
npm run build
```

### Problèmes de Réseau

#### Problème : API calls échouent

**Diagnostic :**
```bash
# Tester API directement
curl -v http://localhost:8000/api/v1/subjects/

# Vérifier réseau Docker
docker network ls
docker network inspect emploi-du-temp_default
```

**Solution :**
```bash
# Dans docker-compose.yml, vérifier que services sont sur même réseau
networks:
  - app_network

# Redémarrer réseau
docker-compose down
docker-compose up -d
```

## 📊 Problèmes de Monitoring

### Prometheus/Grafana

#### Problème : Métriques manquantes

**Diagnostic :**
```bash
# Vérifier endpoint métriques
curl http://localhost:8000/metrics

# Vérifier configuration Prometheus
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml

# Vérifier targets
curl http://localhost:9090/api/v1/targets
```

**Solution :**
```bash
# Redémarrer Prometheus
docker-compose restart prometheus

# Recharger configuration
docker-compose exec prometheus kill -HUP 1
```

#### Problème : Grafana inaccessible

**Solution :**
```bash
# Vérifier Grafana
docker-compose logs grafana

# Reset password admin
docker-compose exec grafana grafana-cli admin reset-admin-password admin

# Accéder: http://localhost:3000 (admin/admin)
```

### Logs

#### Problème : Logs manquants ou illisibles

**Solution :**
```bash
# Configurer niveau de log
export LOG_LEVEL=DEBUG

# Rediriger logs vers fichier
docker-compose logs app > app.log 2>&1

# Analyser logs avec jq (si JSON)
docker-compose logs app | jq '.'
```

## 📋 Collecte d'Informations

### Informations Système

```bash
#!/bin/bash
# Script de collecte d'informations pour support

echo "=== SYSTEM INFO ==="
uname -a
docker version
docker-compose version

echo -e "\n=== RESOURCES ==="
free -h
df -h
docker stats --no-stream

echo -e "\n=== SERVICES STATUS ==="
docker-compose ps

echo -e "\n=== HEALTH CHECKS ==="
curl -s http://localhost:8000/health | jq '.' || echo "API health failed"
curl -s http://localhost:3000/health || echo "Frontend health failed"

echo -e "\n=== RECENT LOGS ==="
docker-compose logs --tail=20 app
docker-compose logs --tail=20 postgres
```

### Informations Application

```bash
#!/bin/bash
# Collecte d'informations application

echo "=== DATABASE INFO ==="
docker-compose exec postgres psql -U school_user -d school_timetable -c "
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables;
"

echo -e "\n=== APP CONFIG ==="
docker-compose exec app python -c "
from app.config.environments import settings
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Debug: {settings.DEBUG}')
print(f'Database: {settings.DATABASE_URL.split(\"@\")[-1] if \"@\" in settings.DATABASE_URL else \"local\"}')
"

echo -e "\n=== RECENT ERRORS ==="
docker-compose logs app | grep -i "error\|exception\|traceback" | tail -10
```

## 🆘 Escalade Support

### Niveaux de Gravité

| Niveau | Description | Délai Réponse | Destinataire |
|--------|-------------|---------------|--------------|
| **P1 - Critique** | Service indisponible | 1 heure | Équipe DevOps |
| **P2 - Élevé** | Fonctionnalité majeure cassée | 4 heures | Support technique |
| **P3 - Moyen** | Problème fonctionnel | 24 heures | Support utilisateur |
| **P4 - Bas** | Amélioration/Question | 72 heures | Documentation |

### Informations à Fournir

#### Pour Problèmes Techniques

```
1. Description détaillée du problème
2. Étapes pour reproduire
3. Comportement attendu vs observé
4. Environnement (dev/staging/prod)
5. Timestamp de l'erreur
6. Logs pertinents
7. Capture d'écran si applicable
```

#### Pour Problèmes Fonctionnels

```
1. Rôle utilisateur
2. Action tentée
3. Message d'erreur exact
4. Données d'entrée utilisées
5. Navigateur et version
6. Historique des actions récentes
```

### Contacts Support

**Support Technique :**
- 📧 Email : support-tech@school-timetable.com
- 💬 Slack : #support-technique
- 📱 Astreinte : +33-6-XX-XX-XX-XX (P1 uniquement)

**Support Utilisateur :**
- 📧 Email : support@school-timetable.com
- 📋 Tickets : https://support.school-timetable.com
- 📞 Téléphone : +33-1-XX-XX-XX-XX

### Templates d'Escalade

#### Template Incident P1

```
OBJET: [P1] Service École Emploi du Temps indisponible

IMPACT:
- Service: [Spécifier]
- Utilisateurs affectés: [Nombre/Tous]
- Début incident: [Timestamp]

SYMPTÔMES:
- [Décrire les symptômes observés]

ACTIONS TENTÉES:
- [Lister les actions déjà effectuées]

LOGS/ERREURS:
[Coller logs pertinents]

CONTACT:
- Nom: [Votre nom]
- Téléphone: [Pour callback urgent]
```

#### Template Bug P2/P3

```
OBJET: [P2/P3] Problème fonctionnel - [Titre court]

ENVIRONNEMENT:
- Instance: [dev/staging/prod]
- Version: [Si connue]
- Navigateur: [Chrome/Firefox/etc.]

REPRODUCTION:
1. [Étape 1]
2. [Étape 2]
3. [Étape 3]

RÉSULTAT ATTENDU:
[Ce qui devrait se passer]

RÉSULTAT OBSERVÉ:
[Ce qui se passe réellement]

LOGS/CAPTURES:
[Joindre fichiers]

URGENCE:
[Justifier niveau de priorité]
```

---

📞 **Support 24/7** : +33-1-XX-XX-XX  
📧 **Email Support** : support@school-timetable.com  
🌐 **Status Page** : https://status.school-timetable.com  

*Dernière mise à jour : v1.0.0 - Mars 2024* 