# Configuration et Initialisation de la Base de Données

## 📋 Résumé de Configuration

✅ **Base de données configurée avec succès !**

### 🏗️ Architecture
- **Type**: SQLite (développement)
- **Fichier**: `backend/school_timetable.db`
- **ORM**: SQLAlchemy 
- **Migrations**: Alembic
- **Tables**: 15 tables créées

### 📊 Tables dans la Base de Données

1. `alembic_version` - Versioning Alembic
2. `users` - Utilisateurs du système
3. `teachers` - Enseignants 
4. `subjects` - Matières
5. `class_groups` - Classes
6. `rooms` - Salles de classe
7. `schedules` - Emplois du temps
8. `schedule_entries` - Entrées d'emploi du temps
9. `schedule_conflicts` - Conflits détectés
10. `teacher_subjects` - Association enseignants-matières
11. `teacher_availabilities` - Disponibilités enseignants
12. `teacher_preferences` - Préférences enseignants
13. `class_subject_requirements` - Exigences matières par classe
14. `room_unavailabilities` - Indisponibilités salles
15. `global_constraints` - Contraintes globales

### ⚙️ Configuration Environnement

```bash
# Variables d'environnement
DATABASE_URL=sqlite:///./school_timetable.db
DEBUG=true
```

### 🚀 Démarrage du Serveur

```powershell
# Méthode 1: Script automatisé (RECOMMANDÉ)
cd backend
./start_server.ps1

# Méthode 2: Manuel
cd backend
$env:DATABASE_URL="sqlite:///./school_timetable.db"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 🔧 Commandes Utiles

```powershell
# Vérifier la base de données
cd backend
python verify_database.py

# Créer une nouvelle migration
$env:DATABASE_URL="sqlite:///./school_timetable.db"
alembic revision --autogenerate -m "Description"

# Appliquer les migrations
alembic upgrade head

# Voir l'état actuel
alembic current

# Voir l'historique
alembic history
```

### 🏥 Vérification de l'État

Pour vérifier que tout fonctionne :

```powershell
cd backend
python verify_database.py
```

### 📚 Documentation API

Une fois le serveur démarré :
- **API Docs**: http://localhost:8000/api/v1/docs
- **Redoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 🔄 Migrations Alembic

**État actuel**: ✅ Version `55d2c0585030` (head)

Le système de migrations est configuré et prêt pour les futures modifications de schéma.

### 🔗 Relations Principales

- `teachers` ↔ `subjects` (many-to-many via `teacher_subjects`)
- `teachers` → `teacher_availabilities` (one-to-many)
- `teachers` → `teacher_preferences` (one-to-many)
- `class_groups` → `class_subject_requirements` (one-to-many)
- `rooms` → `room_unavailabilities` (one-to-many)
- `schedules` → `schedule_entries` (one-to-many)
- `schedules` → `schedule_conflicts` (one-to-many)

### 🇮🇱 Spécificités Israéliennes

- **Semaine**: Dimanche à Jeudi
- **Vendredi court**: Fin à 13h
- **Langues**: Hébreu et Français
- **Heures**: 8h-16h (8h-13h vendredi)

### ✅ Prochaines Étapes

1. **APIs CRUD complètes**: Subjects, Classes, Rooms
2. **Interface frontend**: Pages de gestion
3. **Tests**: Suites de tests complètes
4. **Déploiement**: Configuration production (PostgreSQL)

---

**Status**: 🟢 Base de données fonctionnelle et prête à l'emploi 