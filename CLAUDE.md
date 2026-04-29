# CLAUDE.md

Ce fichier guide Claude Code lorsqu'il travaille sur ce dépôt.

## Vue d'ensemble du projet

Application web de **génération d'emplois du temps scolaires** avec assistance IA, ciblant un établissement bilingue français / hébreu (école israélienne francophone). L'algorithme s'appuie sur **OR-Tools (CP-SAT)** pour résoudre le problème de contraintes, avec une couche d'IA (Claude / OpenAI) pour parser des contraintes en langage naturel et faire des suggestions.

## Stack technique

### Backend (`backend/`)
- **Python 3.11** + **FastAPI 0.109** + **Uvicorn / Gunicorn**
- **SQLAlchemy 2.0** + **Alembic** (migrations)
- **PostgreSQL 15** en prod, **SQLite** en dev
- **Redis 7** + **Celery 5.3** (file de tâches asynchrones, génération longue)
- **OR-Tools 9.8** (solveur CP-SAT pour la combinatoire)
- **Anthropic SDK 0.8.1** + **OpenAI 1.9** (parsing de contraintes, suggestions)
- **python-jose** + **passlib[bcrypt]** (auth JWT)
- **reportlab / openpyxl / icalendar** (export PDF / Excel / iCal)

### Frontend (`frontend/`)
- **React 18.2** + **TypeScript 5.2** + **Vite 4.5**
- **React Router 6.18**
- **Redux Toolkit 1.9** + **TanStack Query 5.8**
- **Tailwind CSS 3.3** + **Headless UI** + **Heroicons**
- **React Hook Form** + **Yup**
- **Axios 1.6**
- **react-hot-toast** (notifications)

### Infrastructure
- **Docker** + **docker-compose** (services : backend, frontend, postgres, redis, nginx, flower, pgadmin, redis-commander)
- **Nginx** comme reverse proxy

## Structure des dossiers

```
emploi-du-temp/
├── backend/
│   ├── app/
│   │   ├── api/api_v1/endpoints/    # auth, teachers, subjects, class_groups,
│   │   │                            # rooms, schedules, import_data, ai, users
│   │   ├── api/api_v1/api.py        # routeur principal
│   │   ├── models/                  # SQLAlchemy : User, Teacher, Subject,
│   │   │                            # ClassGroup, Room, Schedule, Constraint, ...
│   │   ├── schemas/                 # Pydantic
│   │   ├── repositories/            # DAO
│   │   ├── services/                # logique métier
│   │   ├── solver/                  # algo CP-SAT (OR-Tools)
│   │   ├── etl/                     # ShahafImporter (import JSON école)
│   │   ├── ai/                      # intégration Claude / OpenAI
│   │   ├── core/                    # auth.py, config.py, exceptions, logging, metrics
│   │   ├── config/environments.py   # settings (Pydantic)
│   │   ├── db/base.py               # engine, SessionLocal, Base
│   │   ├── db/init_data.py          # seed dev
│   │   └── main.py                  # point d'entrée FastAPI
│   ├── alembic/                     # migrations
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                   # Dashboard, Schedule, Teachers, Subjects,
│   │   │                            # Classes, Rooms, ScheduleGeneration,
│   │   │                            # ImportData, Login
│   │   ├── components/Common/       # Layout, DataTable, FormModal, NotificationSystem
│   │   ├── components/Schedule/     # ScheduleGrid
│   │   ├── components/AI/           # ChatInterface
│   │   ├── services/api.ts          # ApiService Axios
│   │   ├── store/                   # Redux Toolkit slices
│   │   ├── hooks/, contexts/, i18n/, config/
│   │   ├── App.tsx                  # routes
│   │   └── index.tsx                # entrée Vite (référencé par index.html)
│   ├── index.html
│   ├── tailwind.config.js
│   └── package.json
├── docker/                          # nginx/, redis/
├── scripts/
├── docker-compose.yml               # dev
├── docker-compose.prod.yml          # prod
└── .env / env.example
```

## Domaine métier (modèles principaux)

- **User** : `username, email, hashed_password, role` (ADMIN / TEACHER / VIEWER), `language_preference` (he / fr).
- **Teacher** : code, prenom, nom, email, `max_hours_per_week / per_day`, `contract_type`, langues d'enseignement (`can_teach_in_french / hebrew`), relations N-N vers Subject, disponibilités, préférences.
- **Subject** : code, `name_he`, `name_fr`, `subject_type`, couleur, `requires_lab / special_room / consecutive_hours`, `is_religious`, `requires_gender_separation`.
- **ClassGroup** : `name`, `grade` (7-12), `class_type` (regular / special), `student_count`, `homeroom_teacher_id`, M2M vers `mandatory_subjects` et `preferred_rooms`.
- **Room** : code, capacité, `room_type`, `is_lab / is_outdoor`.
- **Schedule** : `status` (draft / active / archived), entrées (ScheduleEntry : teacher × class × room × subject × jour × créneau), conflits.
- **Contraintes** : `TeacherAvailability`, `TeacherPreference`, `RoomUnavailability`, `ClassSubjectRequirement`, `GlobalConstraint`.

## Endpoints API (préfixe `/api/v1`)

- `auth/` : `POST /login` (OAuth2 form), `POST /register`, `POST /logout`, `POST /refresh`
- `teachers/`, `subjects/`, `classes/`, `rooms/` : CRUD standard
- `schedules/` : `GET /`, `POST /generate`, `GET /{id}`, `PUT /{id}/entries`, `GET /{id}/export`
- `import/` : `import-complete-shahaf` (JSON Shahaf), `import-subjects`, `import-classes`, `import-rooms`, `import-enhanced-teachers`, `validate-import-data`
- `ai/` : `POST /chat`, `POST /parse-constraints`, `GET /suggestions/{schedule_id}`
- `/health`, `/` (root)

## Lancer le projet

### Dev local
```bash
# Backend
cd backend
python -m venv venv && source venv/Scripts/activate    # Windows bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8004

# Frontend
cd frontend
npm install
npm run dev
```

### Docker (recommandé)
```bash
docker-compose up -d
# Frontend : http://localhost:3000
# Backend  : http://localhost:8004
# Docs     : http://localhost:8004/docs
```

## Conventions de code

- **Backend** : imports absolus depuis `app.*`. `Base.metadata.create_all` est appelé au lifespan (ne PAS retirer sans utiliser Alembic à la place).
- **Frontend** : composants en PascalCase, hooks en `useXxx`, services en camelCase. Pages dans `pages/`, composants partagés dans `components/Common/`.
- **i18n** : tous les textes affichés doivent passer par `i18n/` (FR / HE), bien que ce ne soit pas encore systématique.
- **RTL** : l'hébreu nécessite `dir="rtl"` — vérifier la prise en charge avant de pousser une nouvelle UI.

## Pièges connus / dette technique

1. **Endpoints `/teachers-test` non authentifiés** utilisés par le frontend (`services/api.ts:86-98`). À supprimer après remise en place de l'auth.
2. **Aucune route protégée dans `App.tsx:35-72`** : pas de `ProtectedRoute`, pas de redirection `/login`. La page `Login.tsx` existe mais n'est pas câblée.
3. **`backend/app/api/api_v1/endpoints/import_data.py:99-132`** génère du SQL par `f-string` (injection SQL). À refaire avec l'ORM.
4. **`import_data.py:46-47`** : bug `name` vs `nom` (NameError au runtime).
5. **Pages Contraintes et Paramètres** sont des stubs « À implémenter » dans `App.tsx`.
6. **`tailwind.config.js`** : aucun breakpoint personnalisé, l'UI est pensée desktop (sidebar fixe `w-64`, tableaux 7 colonnes). Voir section *Mobile* plus bas.
7. **Secrets dans `.env`** committé : `SECRET_KEY`, mots de passe Postgres / pgAdmin par défaut, placeholder de clé Anthropic. À `.gitignore` et régénérer.
8. **`ACCESS_TOKEN_EXPIRE_MINUTES = 7 jours`** dans `core/config.py` — beaucoup trop long.
9. **`localStorage` pour les tokens** (`api.ts:20`) — vulnérable XSS, préférer cookie httpOnly.
10. **`any` partout dans `services/api.ts`** au lieu de types réels — supprime l'intérêt de TypeScript.
11. **Mocks dans `pages/Schedule.tsx:40-53`** : `handleExport` et `handleAIMessage` ne font qu'un `console.log`, pas d'appel API.
12. **`index.html` référence `/src/index.tsx`** (et non `main.tsx`) — à connaître si on touche au point d'entrée Vite.

## Avant de modifier l'UI

- L'application doit fonctionner sur **mobile** : tester systématiquement à 375 px de large. Les tableaux denses (`ScheduleGrid`, `DataTable`) sont les premiers points de friction. Voir la roadmap mobile dans le rapport d'analyse.
- Sur les pages Schedule / Teachers / Subjects / Classes / Rooms, vérifier le scroll horizontal sur petit écran avant de pousser.
- Tout nouveau formulaire : `inputs` en `text-base` (pas `text-sm`) pour éviter le zoom iOS, et `min-h-[44px]` sur les boutons (cible tactile Apple HIG).

## Avant de modifier le backend

- Les imports Shahaf passent par `etl/ShahafImporter`. Si on touche aux modèles, vérifier que l'importer n'est pas cassé (pas de tests qui le couvrent à fond).
- Le solveur (`solver/`) consomme les `Constraint*` ; toute migration de modèle doit être vérifiée côté solveur.
- Un appel à `POST /schedules/generate` peut être long : passer par Celery (`celery_app`) plutôt que par la requête HTTP directement pour les gros volumes.

## Outils de debug

- `docker-compose logs -f backend` / `frontend`
- pgAdmin : `localhost:5050`
- Redis Commander : `localhost:8081`
- Flower (Celery) : `localhost:5555`
- Swagger : `localhost:8004/docs`
