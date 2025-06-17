# 🚀 Guide de Déploiement - École Emploi du Temps

Ce guide détaille le déploiement de l'application École Emploi du Temps pour tous les environnements : développement, staging et production.

## 📋 Table des Matières

- [Prérequis](#prérequis)
- [Déploiement Local](#déploiement-local)
- [Déploiement Staging](#déploiement-staging)
- [Déploiement Production](#déploiement-production)
- [Configuration Monitoring](#configuration-monitoring)
- [Maintenance & Backup](#maintenance--backup)
- [Troubleshooting](#troubleshooting)
- [Sécurité](#sécurité)

## 🛠️ Prérequis

### Matériel Minimum

| Environnement | CPU | RAM | Stockage | Réseau |
|---------------|-----|-----|----------|--------|
| **Développement** | 2 cores | 4 GB | 10 GB | 1 Mbps |
| **Staging** | 2 cores | 8 GB | 50 GB | 10 Mbps |
| **Production** | 4 cores | 16 GB | 200 GB | 100 Mbps |

### Logiciels Requis

**Tous Environnements :**
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+
- Curl/wget

**Production Additionnels :**
- Traefik 3.0+
- Certbot (Let's Encrypt)
- Backup tools (rsync, aws-cli)

### Accès Réseau

**Ports Requis :**
- `80` : HTTP (redirect HTTPS)
- `443` : HTTPS
- `8080` : Traefik Dashboard
- `22` : SSH (administration)

**Domaines/Sous-domaines :**
- `app.yourdomain.com` : Application principale
- `api.yourdomain.com` : API backend
- `grafana.yourdomain.com` : Monitoring
- `prometheus.yourdomain.com` : Métriques

## 🏠 Déploiement Local

### Installation Rapide

```bash
# Cloner le repository
git clone https://github.com/your-org/school-timetable.git
cd school-timetable

# Copier la configuration d'exemple
cp .env.example .env

# Ajuster les variables d'environnement
nano .env

# Démarrage avec données de démonstration
./quick_start_with_data.ps1
```

### Configuration Manuelle

#### 1. Variables d'Environnement

```bash
# .env
ENVIRONMENT=development
DEBUG=true

# Base de données
DATABASE_URL=sqlite:///./school_timetable.db

# Sécurité (générer avec openssl rand -hex 32)
SECRET_KEY=your-dev-secret-key-here
JWT_SECRET_KEY=your-dev-jwt-secret-key-here

# CORS (permissif en dev)
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# APIs externes (optionnel)
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=

# Features flags (tous activés en dev)
FEATURE_TIMETABLE_AI=true
FEATURE_ADVANCED_ANALYTICS=true
FEATURE_MOBILE_PUSH=false
FEATURE_EXPORT_PDF=true
FEATURE_BACKUP_AUTO=false
```

#### 2. Démarrage Services

```bash
# Démarrage en mode développement
docker-compose -f docker-compose.dev.yml up -d

# Vérification statut
docker-compose -f docker-compose.dev.yml ps

# Logs en temps réel
docker-compose -f docker-compose.dev.yml logs -f
```

#### 3. Initialisation Base de Données

```bash
# Migrations
docker-compose -f docker-compose.dev.yml exec app alembic upgrade head

# Données de test
docker-compose -f docker-compose.dev.yml exec app python scripts/load_test_data.py

# Créer un utilisateur admin
docker-compose -f docker-compose.dev.yml exec app python create_test_user.py
```

### Accès Local

- **Frontend** : http://localhost:3000
- **API** : http://localhost:8000
- **Docs API** : http://localhost:8000/docs
- **Mailhog** : http://localhost:8025

## 🧪 Déploiement Staging

### Configuration Serveur

#### 1. Préparation Serveur

```bash
# Connexion au serveur
ssh user@staging-server

# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Installation Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Redémarrage session
exit && ssh user@staging-server
```

#### 2. Configuration Application

```bash
# Cloner le repository
git clone https://github.com/your-org/school-timetable.git /opt/school-timetable
cd /opt/school-timetable

# Configuration staging
cp .env.staging.example .env
```

#### 3. Variables d'Environnement Staging

```bash
# .env
ENVIRONMENT=staging
DEBUG=false

# Base de données PostgreSQL
DATABASE_URL=postgresql://school_user:${DB_PASSWORD}@postgres:5432/school_timetable_staging
DB_PASSWORD=staging-secure-password-here

# Sécurité
SECRET_KEY=staging-secret-key-32-characters-min
JWT_SECRET_KEY=staging-jwt-secret-key-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["https://staging.yourdomain.com"]

# Email (service staging)
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=staging@yourdomain.com
SMTP_PASSWORD=staging-email-password

# Monitoring
GRAFANA_PASSWORD=staging-grafana-password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/staging/webhook

# Features (certaines désactivées)
FEATURE_MOBILE_PUSH=false
FEATURE_BACKUP_AUTO=true
```

#### 4. Déploiement

```bash
# Build et démarrage
docker-compose -f docker-compose.staging.yml up -d

# Vérification santé
curl -f http://localhost/health

# Initialisation base de données
docker-compose -f docker-compose.staging.yml exec app alembic upgrade head
```

### Tests Post-Déploiement

```bash
# Tests de fumée
docker-compose -f docker-compose.staging.yml exec app python -m pytest tests/smoke/ -v

# Tests d'intégration
docker-compose -f docker-compose.staging.yml exec app python -m pytest tests/integration/ -v

# Tests de charge légers
docker-compose -f docker-compose.staging.yml exec app python scripts/load_test.py --users 10 --duration 60
```

## 🏭 Déploiement Production

### Architecture Production

```
Internet
    ↓
[Cloudflare/CDN] ← SSL/DDoS Protection
    ↓
[Load Balancer] ← Traefik
    ↓
[Application Stack]
├── Frontend (Nginx)
├── Backend (FastAPI)
├── Database (PostgreSQL)
├── Cache (Redis)
└── Monitoring (Prometheus/Grafana)
```

### Préparation Infrastructure

#### 1. Configuration DNS

```bash
# Enregistrements DNS requis
app.yourdomain.com       A    YOUR_SERVER_IP
api.yourdomain.com       A    YOUR_SERVER_IP
grafana.yourdomain.com   A    YOUR_SERVER_IP
prometheus.yourdomain.com A   YOUR_SERVER_IP
```

#### 2. Certificats SSL

```bash
# Installation Certbot
sudo apt install certbot

# Génération certificats
sudo certbot certonly --standalone -d yourdomain.com -d *.yourdomain.com

# Vérification renouvellement automatique
sudo crontab -e
# Ajouter: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Configuration Production

#### 1. Variables d'Environnement Production

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false

# Domaine
DOMAIN=yourdomain.com
ACME_EMAIL=admin@yourdomain.com

# Base de données (RDS/PostgreSQL dédié)
PRODUCTION_DATABASE_URL=postgresql://user:password@db.yourdomain.com:5432/school_timetable
DB_PASSWORD=ultra-secure-production-password

# Sécurité (clés longues et aléatoires)
PRODUCTION_SECRET_KEY=production-secret-key-64-characters-minimum-length
PRODUCTION_JWT_SECRET_KEY=production-jwt-secret-key-64-characters-minimum
ACCESS_TOKEN_EXPIRE_MINUTES=15

# CORS strict
PRODUCTION_CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]

# Cache Redis (ElastiCache/Redis dédié)
PRODUCTION_REDIS_URL=redis://redis.yourdomain.com:6379/0

# Email production
PRODUCTION_SMTP_HOST=smtp.sendgrid.net
PRODUCTION_SMTP_USERNAME=apikey
PRODUCTION_SMTP_PASSWORD=your-sendgrid-api-key

# Monitoring
GRAFANA_PASSWORD=production-grafana-ultra-secure-password
TRAEFIK_AUTH=admin:$2y$10$hashed_password_here

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/production/webhook

# Backup
BACKUP_S3_BUCKET=school-timetable-backups
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# Features production
FEATURE_MOBILE_PUSH=true
FEATURE_BACKUP_AUTO=true
```

#### 2. Optimisations Système

```bash
# Limites système
echo "fs.file-max = 65536" >> /etc/sysctl.conf
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
sysctl -p

# Swap (si RAM < 16GB)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Firewall
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp
```

### Déploiement Production

#### 1. Déploiement Initial

```bash
# Répertoire application
sudo mkdir -p /opt/school-timetable
sudo chown $USER:$USER /opt/school-timetable
cd /opt/school-timetable

# Clone repository
git clone https://github.com/your-org/school-timetable.git .

# Configuration
cp .env.production.example .env
# Éditer avec vos valeurs de production

# Permissions sécurisées
chmod 600 .env
```

#### 2. Premier Démarrage

```bash
# Pull des images
docker-compose -f docker-compose.prod.yml pull

# Démarrage base de données d'abord
docker-compose -f docker-compose.prod.yml up -d postgres redis

# Attendre démarrage
sleep 30

# Migrations
docker-compose -f docker-compose.prod.yml exec postgres psql -U school_user -d school_timetable -c "SELECT 1;"
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# Démarrage complet
docker-compose -f docker-compose.prod.yml up -d

# Vérification
curl -f https://yourdomain.com/health
```

#### 3. Configuration Monitoring

```bash
# Création utilisateur Grafana admin
docker-compose -f docker-compose.prod.yml exec grafana grafana-cli admin reset-admin-password $GRAFANA_PASSWORD

# Import dashboards
curl -X POST \
  -H "Content-Type: application/json" \
  -d @docker/grafana/dashboards/school-timetable-overview.json \
  http://admin:$GRAFANA_PASSWORD@localhost:3000/api/dashboards/db
```

### Tests Production

#### 1. Tests de Santé

```bash
# Health checks
curl -f https://yourdomain.com/health
curl -f https://api.yourdomain.com/health
curl -f https://grafana.yourdomain.com/api/health

# Tests API
curl -X GET https://api.yourdomain.com/api/v1/subjects/ \
  -H "Authorization: Bearer $TOKEN"

# Tests base de données
docker-compose -f docker-compose.prod.yml exec app python -c "
from app.core.database import get_db
from sqlalchemy import text
for db in get_db():
    result = db.execute(text('SELECT COUNT(*) FROM subjects'))
    print(f'Subjects count: {result.scalar()}')
    break
"
```

#### 2. Tests de Charge

```bash
# Installation outils
sudo apt install apache2-utils

# Test charge API
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" \
  https://api.yourdomain.com/api/v1/subjects/

# Test charge frontend
ab -n 1000 -c 10 https://yourdomain.com/

# Monitoring pendant les tests
docker-compose -f docker-compose.prod.yml exec prometheus promtool query instant 'rate(http_requests_total[5m])'
```

## 📊 Configuration Monitoring

### Métriques Prometheus

#### 1. Configuration Prometheus

```yaml
# docker/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/prometheus/rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'school-timetable-app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'traefik'
    static_configs:
      - targets: ['traefik:8080']
```

#### 2. Règles d'Alertes

```yaml
# docker/prometheus/rules/school-timetable.yml
groups:
  - name: school-timetable-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      - alert: DatabaseDown
        expr: up{job="postgres-exporter"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"
          description: "PostgreSQL database is not responding"

      - alert: LowDiskSpace
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space"
          description: "Disk space is below 10%"
```

### Dashboards Grafana

#### 1. Dashboard Principal

```json
{
  "dashboard": {
    "title": "School Timetable - Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "req/s"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m])",
            "legendFormat": "errors/s"
          }
        ]
      },
      {
        "title": "Response Time P95",
        "type": "stat",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p95"
          }
        ]
      }
    ]
  }
}
```

## 💾 Maintenance & Backup

### Backup Automatique

#### 1. Configuration Backup

```bash
# Script de backup quotidien
sudo crontab -e

# Ajouter:
0 2 * * * /opt/school-timetable/scripts/backup.sh
0 4 * * 0 /opt/school-timetable/scripts/cleanup-old-backups.sh
```

#### 2. Test Backup

```bash
# Test backup manuel
./scripts/backup.sh --dry-run

# Backup complet
./scripts/backup.sh

# Vérification backup
ls -la backups/
```

### Restauration

#### 1. Restauration Base de Données

```bash
# Arrêter l'application
docker-compose -f docker-compose.prod.yml down

# Restaurer depuis backup
./scripts/restore.sh backup_20240101_120000.sql.gz

# Redémarrer
docker-compose -f docker-compose.prod.yml up -d
```

#### 2. Rollback Complet

```bash
# Rollback automatique en cas d'échec
./scripts/rollback.sh "deployment-failed"

# Vérification post-rollback
curl -f https://yourdomain.com/health
```

### Maintenance Préventive

#### 1. Nettoyage Régulier

```bash
# Script de nettoyage hebdomadaire
#!/bin/bash

# Nettoyage Docker
docker system prune -f
docker volume prune -f

# Nettoyage logs
find /var/log -name "*.log" -mtime +30 -delete

# Nettoyage backups anciens
find /opt/school-timetable/backups -name "*.gz" -mtime +30 -delete

# Optimisation base de données
docker-compose -f docker-compose.prod.yml exec postgres psql -U school_user -d school_timetable -c "VACUUM ANALYZE;"
```

#### 2. Monitoring Santé

```bash
# Script de vérification quotidienne
#!/bin/bash

# Health checks
curl -f https://yourdomain.com/health || echo "ALERT: App health check failed"
curl -f https://api.yourdomain.com/health || echo "ALERT: API health check failed"

# Métriques système
df -h | grep -E '9[0-9]%' && echo "ALERT: Disk space > 90%"
free -m | awk 'NR==2{printf "Memory Usage: %s/%sMB (%.2f%%)\n", $3,$2,$3*100/$2 }'

# Services Docker
docker-compose -f docker-compose.prod.yml ps | grep -v "Up" && echo "ALERT: Some services are down"
```

## 🔒 Sécurité

### Checklist Sécurité

#### 1. Configuration Serveur

- [ ] **Firewall** : UFW configuré avec ports minimum
- [ ] **SSH** : Clés uniquement, désactiver password auth
- [ ] **Fail2ban** : Protection brute force
- [ ] **Updates** : Automatiques pour sécurité
- [ ] **Users** : Utilisateurs minimum, sudo restreint

```bash
# Configuration sécurité de base
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# SSH sécurisé
echo "PasswordAuthentication no" >> /etc/ssh/sshd_config
echo "PermitRootLogin no" >> /etc/ssh/sshd_config
sudo systemctl restart ssh

# Fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

#### 2. Configuration Application

- [ ] **Secrets** : Variables d'environnement sécurisées
- [ ] **HTTPS** : Certificats valides, HSTS
- [ ] **CORS** : Origines strictement définies
- [ ] **JWT** : Expiration courte, rotation clés
- [ ] **Rate Limiting** : Protection API

```bash
# Vérification sécurité
docker-compose -f docker-compose.prod.yml exec app python -c "
from app.config.environments import settings
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Debug: {settings.DEBUG}')
print(f'Secret key length: {len(settings.SECRET_KEY)}')
print(f'CORS origins: {settings.CORS_ORIGINS}')
"
```

### Audit Sécurité

#### 1. Scan Vulnérabilités

```bash
# Scan containers
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image school-timetable/app:latest

# Scan filesystem
docker run --rm -v $(pwd):/src \
  aquasec/trivy fs /src
```

#### 2. Tests Pénétration

```bash
# Test basic avec nmap
nmap -sS -O yourdomain.com

# Test SSL
sslscan yourdomain.com

# Test headers sécurité
curl -I https://yourdomain.com | grep -E "(Strict-Transport-Security|Content-Security-Policy|X-Frame-Options)"
```

## 🔧 Troubleshooting

### Problèmes Courants

#### 1. Service ne démarre pas

```bash
# Vérifier logs
docker-compose -f docker-compose.prod.yml logs app

# Vérifier configuration
docker-compose -f docker-compose.prod.yml config

# Vérifier ressources
docker stats
```

#### 2. Base de données inaccessible

```bash
# Test connectivité
docker-compose -f docker-compose.prod.yml exec app python -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('DB connection OK')
"

# Vérifier PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U school_user
```

#### 3. Performance dégradée

```bash
# Métriques temps réel
docker-compose -f docker-compose.prod.yml exec prometheus promtool query instant 'rate(http_requests_total[5m])'

# Analyse logs lents
docker-compose -f docker-compose.prod.yml logs app | grep "SLOW"

# Stats base de données
docker-compose -f docker-compose.prod.yml exec postgres psql -U school_user -d school_timetable -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
"
```

### Contacts Support

**Urgences Production :**
- Email : ops@yourdomain.com
- Slack : #production-alerts
- Phone : +XX-XXX-XXX-XXX

**Support Technique :**
- GitHub Issues : https://github.com/your-org/school-timetable/issues
- Documentation : https://docs.school-timetable.com
- Status Page : https://status.school-timetable.com

---

📝 **Ce guide est maintenu à jour avec chaque release. Dernière mise à jour : v1.0.0** 