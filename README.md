# 🏫 École Emploi du Temps - Système de Gestion d'Emplois du Temps

[![CI/CD Pipeline](https://github.com/your-org/school-timetable/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/your-org/school-timetable/actions)
[![codecov](https://codecov.io/gh/your-org/school-timetable/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/school-timetable)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://hub.docker.com/r/schooltimetable/app)

Une application web complète pour la gestion d'emplois du temps scolaires avec support bilingue (Français/Hébreu), génération automatique optimisée et interface utilisateur moderne.

## 🌟 Fonctionnalités

### 📚 Gestion Académique
- **Matières** : CRUD complet avec support bilingue, codes uniques, niveaux requis
- **Classes** : Organisation par niveau, effectifs, matières obligatoires, horaires préférés  
- **Salles** : Capacités, équipements, disponibilités, types spécialisés
- **Enseignants** : Profils complets, spécialisations, contraintes horaires

### 🤖 Génération Intelligente
- **Algorithme Optimisé** : Génération automatique avec contraintes multiples
- **Résolution de Conflits** : Détection et résolution automatique des incompatibilités
- **Optimisation** : Minimisation des trous, répartition équilibrée
- **Validation** : Vérification exhaustive des contraintes métier

### 🌐 Interface Utilisateur
- **Design Moderne** : Interface responsive avec Tailwind CSS
- **Support Bilingue** : Français/Hébreu avec RTL automatique
- **Accessibilité** : Conforme WCAG 2.1 AA
- **Performance** : Optimisations poussées, lazy loading

### 🔐 Sécurité & Administration
- **Authentification JWT** : Sécurisée avec refresh tokens
- **Autorisation RBAC** : Rôles et permissions granulaires
- **Audit Trail** : Logs complets des actions utilisateurs
- **Rate Limiting** : Protection contre les abus

### 📊 Monitoring & Observabilité
- **Métriques Prometheus** : Performance, erreurs, utilisation
- **Logs Structurés** : JSON avec corrélation IDs
- **Health Checks** : Surveillance proactive
- **Alerting** : Notifications automatiques

## 🚀 Démarrage Rapide

### Prérequis
- Docker 20.10+
- Docker Compose 2.0+
- Git

### Installation Express

```bash
# Cloner le projet
git clone https://github.com/your-org/school-timetable.git
cd school-timetable

# Démarrage rapide avec données de démonstration
./quick_start_with_data.ps1
```

L'application sera accessible sur :
- **Frontend** : http://localhost:3000
- **API** : http://localhost:8000
- **Documentation** : http://localhost:8000/docs

### Configuration Personnalisée

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer les variables d'environnement
nano .env

# Démarrer avec votre configuration
docker-compose up -d
```

## 📖 Documentation

### Guides Utilisateur
- [**Guide Utilisateur Français**](docs/USER_GUIDE_FR.md)
- [**Guide Utilisateur Hébreu**](docs/USER_GUIDE_HE.md)
- [**Tutoriels Vidéo**](docs/VIDEO_TUTORIALS.md)
- [**FAQ**](docs/FAQ.md)

### Documentation Technique
- [**Architecture Détaillée**](ARCHITECTURE.md)
- [**API Documentation**](docs/API_DOCS.md)
- [**Guide de Déploiement**](DEPLOYMENT.md)
- [**Guide de Développement**](docs/DEVELOPMENT.md)
- [**Troubleshooting**](docs/TROUBLESHOOTING.md)

### Spécifications APIs
- [**Subjects API**](SUBJECTS_API_DOCUMENTATION.md)
- [**ClassGroups & Rooms API**](CLASSGROUPS_ROOMS_API_DOCUMENTATION.md)
- [**Authentication API**](docs/AUTH_API.md)
- [**Timetable Generation API**](docs/TIMETABLE_API.md)

## 🏗️ Architecture

### Stack Technologique

**Backend**
- FastAPI 0.104+ (Python 3.11)
- SQLAlchemy 2.0 + Alembic
- PostgreSQL 15 / SQLite
- Redis pour le cache
- Celery pour les tâches asynchrones

**Frontend**
- React 18 + TypeScript
- Tailwind CSS + Headless UI
- React Query pour l'état serveur
- React Hook Form + Zod

**Infrastructure**
- Docker + Docker Compose
- Traefik pour le reverse proxy
- Prometheus + Grafana
- Loki + Promtail pour les logs

### Diagramme d'Architecture

```mermaid
graph TB
    subgraph "Frontend"
        A[React App] --> B[API Client]
    end
    
    subgraph "Backend Services"
        C[FastAPI] --> D[Authentication]
        C --> E[Business Logic]
        C --> F[Timetable Engine]
    end
    
    subgraph "Data Layer"
        G[PostgreSQL] --> H[SQLAlchemy ORM]
        I[Redis Cache] --> J[Session Store]
    end
    
    subgraph "Infrastructure"
        K[Traefik] --> L[Load Balancer]
        M[Prometheus] --> N[Metrics]
        O[Grafana] --> P[Dashboards]
    end
    
    A --> K
    K --> C
    E --> H
    E --> J
```

## 🚀 Déploiement Production

### Configuration Environnement

```bash
# Variables essentielles
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
export SECRET_KEY=your-super-secret-key
export CORS_ORIGINS=https://yourdomain.com
```

### Déploiement Docker

```bash
# Build et déploiement production
docker-compose -f docker-compose.prod.yml up -d

# Vérification santé
curl -f https://yourdomain.com/health
```

### Monitoring

**Accès aux interfaces :**
- **Grafana** : https://grafana.yourdomain.com
- **Prometheus** : https://prometheus.yourdomain.com
- **AlertManager** : https://alertmanager.yourdomain.com

**Métriques clés surveillées :**
- Temps de réponse API (< 200ms P95)
- Taux d'erreur (< 1%)
- Utilisation CPU/Mémoire
- Générations d'emplois du temps

## 🔧 Développement

### Setup Environnement Dev

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm start
```

### Tests

```bash
# Backend
cd backend
pytest tests/ -v --cov=app

# Frontend  
cd frontend
npm test
npm run test:e2e
```

### Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/amazing-feature`)
3. Commiter les changements (`git commit -m 'Add amazing feature'`)
4. Pousser vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

## 📊 Statistiques Projet

```
Lignes de Code    : ~25,000
Tests             : 450+ 
Couverture        : 90%+
Documentation     : 15+ guides
Langues           : 2 (FR/HE)
APIs              : 40+ endpoints
```

## 🛠️ Outils Intégrés

### Développement
- **Hot Reload** : Rechargement automatique
- **TypeScript** : Typage statique complet
- **ESLint/Prettier** : Qualité code
- **Storybook** : Composants UI

### CI/CD
- **GitHub Actions** : Pipeline automatisé
- **Tests Automatisés** : Unit, intégration, E2E
- **Security Scanning** : CodeQL, Trivy
- **Déploiement Automatique** : Staging/Production

### Monitoring
- **Logs Structurés** : JSON avec corrélation
- **Métriques Business** : Générations, utilisateurs
- **Alertes Intelligentes** : Slack/Email
- **Health Checks** : Probes Kubernetes

## 🚨 Alertes & Monitoring

### Alertes Configurées
- **Erreurs Critiques** : Taux > 5%
- **Performance Dégradée** : P95 > 500ms  
- **Santé Base de Données** : Connexions échouées
- **Espace Disque** : < 10% libre
- **Certificats SSL** : Expiration < 30 jours

### Dashboards Grafana
- **Vue d'Ensemble** : Métriques générales
- **Performance API** : Endpoints détaillés
- **Business Intelligence** : Utilisation métier
- **Infrastructure** : Système et réseau

## 📋 Roadmap

### Version 1.1 (Q2 2024)
- [ ] Notifications push mobile
- [ ] Export PDF avancé
- [ ] Intégration calendrier externe
- [ ] API webhooks

### Version 1.2 (Q3 2024)
- [ ] Intelligence artificielle optimisation
- [ ] Multi-tenant support
- [ ] API GraphQL
- [ ] Application mobile native

### Version 2.0 (Q4 2024)
- [ ] Microservices architecture
- [ ] Kubernetes deployment
- [ ] Advanced analytics
- [ ] Machine learning insights

## 🤝 Support

### Communauté
- **Discord** : https://discord.gg/school-timetable
- **Forum** : https://forum.school-timetable.com
- **GitHub Discussions** : https://github.com/your-org/school-timetable/discussions

### Support Commercial
- **Email** : support@school-timetable.com
- **Documentation** : https://docs.school-timetable.com
- **Status Page** : https://status.school-timetable.com

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👥 Équipe

### Mainteneurs
- **Lead Developer** : [@username](https://github.com/username)
- **DevOps Engineer** : [@devops-user](https://github.com/devops-user)
- **UI/UX Designer** : [@designer](https://github.com/designer)

### Contributeurs
Merci à tous les [contributeurs](https://github.com/your-org/school-timetable/graphs/contributors) qui ont participé à ce projet !

---

⭐ **N'hésitez pas à donner une étoile si ce projet vous est utile !** ⭐ 