# Architecture de l'Application de Génération d'Emplois du Temps

## Vue d'Ensemble

Cette application est une solution complète de génération d'emplois du temps scolaires avec un agent IA intégré, conçue spécifiquement pour les établissements israéliens avec support bilingue français/hébreu.

## Architecture Technique

### 1. Frontend (React + TypeScript)

#### Structure des Composants
```
src/
├── components/
│   ├── Schedule/
│   │   ├── ScheduleGrid.tsx      # Grille principale d'affichage
│   │   ├── ScheduleEntry.tsx     # Entrée individuelle
│   │   └── DragDropWrapper.tsx   # Gestion du drag & drop
│   ├── AI/
│   │   ├── ChatInterface.tsx     # Interface de chat avec l'IA
│   │   ├── ConstraintForm.tsx    # Formulaire de contraintes
│   │   └── SuggestionsList.tsx   # Liste des suggestions IA
│   └── Common/
│       ├── Layout.tsx            # Layout principal
│       ├── Navigation.tsx        # Navigation
│       └── LanguageSelector.tsx  # Sélecteur de langue
├── services/
│   ├── api.ts                    # Client API Axios
│   ├── auth.service.ts           # Gestion de l'authentification
│   ├── schedule.service.ts       # Services emplois du temps
│   └── ai.service.ts             # Services agent IA
├── store/                        # Redux store
│   ├── slices/
│   │   ├── authSlice.ts
│   │   ├── scheduleSlice.ts
│   │   └── aiSlice.ts
│   └── store.ts
└── i18n/                         # Internationalisation
    ├── fr.json
    └── he.json
```

#### Technologies Clés
- **React 18** avec hooks et composants fonctionnels
- **TypeScript** pour le typage fort
- **Material-UI** pour les composants UI
- **Redux Toolkit** pour la gestion d'état
- **React Beautiful DnD** pour le drag & drop
- **i18next** pour l'internationalisation
- **Formik + Yup** pour les formulaires et validation

### 2. Backend (FastAPI + Python)

#### Architecture en Couches
```
backend/
├── app/
│   ├── api/                     # Couche API
│   │   └── api_v1/
│   │       └── endpoints/       # Points d'entrée REST
│   ├── core/                    # Configuration & Sécurité
│   │   ├── config.py           # Configuration centralisée
│   │   └── auth.py             # Authentification JWT
│   ├── models/                  # Modèles SQLAlchemy
│   │   ├── user.py
│   │   ├── teacher.py
│   │   ├── subject.py
│   │   ├── class_group.py
│   │   ├── room.py
│   │   ├── constraint.py
│   │   └── schedule.py
│   ├── schemas/                 # Schémas Pydantic
│   │   └── [corresponding schemas]
│   ├── services/                # Logique métier
│   ├── solver/                  # Moteur d'optimisation
│   │   └── timetable_solver.py # OR-Tools CP-SAT
│   └── ai/                      # Agent IA
│       └── agent.py            # Intégration Claude/GPT
```

#### Composants Principaux

##### 1. Moteur d'Optimisation (OR-Tools)
- Utilise **Google OR-Tools CP-SAT** pour la résolution
- Gestion des contraintes dures et souples
- Support des spécificités israéliennes :
  - Semaine du dimanche au vendredi
  - Vendredi écourté (fin à 13h)
  - Séparation garçons/filles pour certains cours
  - Matières religieuses spécifiques

##### 2. Agent IA
- Support **Claude (Anthropic)** et **GPT (OpenAI)**
- Fonctionnalités :
  - Parsing de contraintes en langage naturel
  - Explication des conflits en termes non-techniques
  - Suggestions d'amélioration contextuelles
  - Support bilingue français/hébreu

##### 3. API REST
- Architecture RESTful avec FastAPI
- Documentation automatique (OpenAPI/Swagger)
- Authentification JWT avec rôles (Admin, Teacher, Viewer)
- Validation des données avec Pydantic

### 3. Base de Données (PostgreSQL)

#### Schéma Principal
```sql
-- Utilisateurs et authentification
users (id, email, username, hashed_password, role, language_preference)

-- Entités principales
teachers (id, code, first_name, last_name, max_hours_per_week, languages)
subjects (id, code, name_he, name_fr, type, requirements)
class_groups (id, code, name, grade, student_count, gender_settings)
rooms (id, code, name, type, capacity, features)

-- Contraintes
teacher_availabilities (teacher_id, day, start_time, end_time)
room_unavailabilities (room_id, day, start_time, end_time)
class_subject_requirements (class_id, subject_id, hours_per_week)
global_constraints (name, type, parameters)

-- Emplois du temps
schedules (id, name, status, solver_status, generation_time)
schedule_entries (schedule_id, day, period, class_id, teacher_id, room_id, subject_id)
schedule_conflicts (schedule_id, type, description, suggestions)

-- Relations many-to-many
teacher_subjects (teacher_id, subject_id)
```

### 4. Infrastructure et Services

#### Docker Compose Services
1. **PostgreSQL** : Base de données principale
2. **Redis** : Cache et broker de messages
3. **Backend API** : Application FastAPI
4. **Celery Worker** : Traitement asynchrone
5. **Flower** : Monitoring des tâches Celery
6. **Frontend** : Application React
7. **Nginx** : Reverse proxy (production)

#### Flux de Données
1. **Génération d'emploi du temps** :
   - L'utilisateur soumet une requête via l'UI
   - L'API crée une tâche Celery
   - Le worker lance le solver OR-Tools
   - Les résultats sont stockés en DB
   - L'UI est notifiée via WebSocket/polling

2. **Interaction avec l'Agent IA** :
   - L'utilisateur saisit du texte en langage naturel
   - L'API transmet à Claude/GPT
   - L'IA parse et retourne des actions structurées
   - Le backend applique les modifications
   - L'UI affiche les changements

## Contraintes Gérées

### Contraintes Dures (Obligatoires)
1. **Disponibilité des enseignants**
2. **Disponibilité des salles**
3. **Pas de conflits** (enseignant/salle/classe)
4. **Heures requises par matière**
5. **Capacité des salles**
6. **Équipements spécifiques** (labo, sport, etc.)

### Contraintes Souples (Optimisation)
1. **Minimiser les trous** dans l'emploi du temps des enseignants
2. **Heures consécutives** pour certaines matières
3. **Répartition équilibrée** sur la semaine
4. **Préférences des enseignants**
5. **Pauses déjeuner**
6. **Charge équilibrée** entre enseignants

### Spécificités Israéliennes
1. **Vendredi court** (fin à 13h)
2. **Séparation garçons/filles** pour sport/religion
3. **Prière du vendredi**
4. **Matières religieuses** spécifiques
5. **Bilinguisme** hébreu/français

## Sécurité

1. **Authentification JWT** avec refresh tokens
2. **Rôles et permissions** (RBAC)
3. **Validation des entrées** (Pydantic)
4. **CORS configuré**
5. **Variables d'environnement** pour les secrets
6. **HTTPS en production** (via Nginx)
7. **Anonymisation** des données pour l'IA

## Performance et Scalabilité

1. **Cache Redis** pour les résultats fréquents
2. **Tâches asynchrones** avec Celery
3. **Pagination** des résultats API
4. **Optimisation des requêtes** SQL
5. **Limite de temps** pour le solver
6. **Load balancing** possible avec plusieurs workers

## Monitoring et Maintenance

1. **Logs structurés** (JSON)
2. **Flower** pour monitoring Celery
3. **Health checks** pour tous les services
4. **Métriques de performance** du solver
5. **Versioning** des emplois du temps
6. **Backup automatique** de la DB

## Déploiement

### Développement
```bash
docker-compose up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml --profile production up -d
```

### Variables d'Environnement Requises
- `ANTHROPIC_API_KEY` ou `OPENAI_API_KEY`
- `SECRET_KEY` pour JWT
- `DATABASE_URL` en production
- `REDIS_URL` en production

## Points d'Extension

1. **Nouveaux types de contraintes** dans le solver
2. **Intégration avec systèmes existants** (import/export)
3. **Notifications en temps réel** (WebSocket)
4. **Application mobile** (API REST existante)
5. **Rapports et statistiques** avancés
6. **Multi-établissements** (SaaS) 