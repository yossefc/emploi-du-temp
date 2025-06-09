# 🎓 Générateur d'Emplois du Temps avec IA

Une application complète de génération d'emplois du temps scolaires avec agent IA intégré, spécialement conçue pour les établissements israéliens avec support bilingue français/hébreu.

## 🚀 Démarrage Rapide

### Configuration SQLite (Recommandée pour le développement)

```powershell
# 1. Cloner et installer les dépendances
git clone <votre-repo>
cd emploi-du-temps

# 2. Installation Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd ..

# 3. Installation Frontend  
cd frontend
npm install
cd ..

# 4. Démarrage avec SQLite (Simple et rapide)
.\start_with_sqlite.ps1
```

### Accès à l'Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000  
- **Documentation API**: http://localhost:8000/api/v1/docs

### Connexion de Test

```
Email: admin@example.com
Mot de passe: password123
```

## 🏗️ Architecture

### Stack Technique
- **Frontend**: React + TypeScript + Material-UI + Redux
- **Backend**: FastAPI + Python + SQLAlchemy + OR-Tools  
- **Base de données**: SQLite (développement) / PostgreSQL (production)
- **Agent IA**: Claude (Anthropic) / GPT (OpenAI)
- **Solver**: Google OR-Tools CP-SAT

### Structure du Projet
```
emploi-du-temps/
├── backend/              # API FastAPI
│   ├── app/
│   │   ├── api/         # Endpoints REST
│   │   │   ├── models/      # Modèles SQLAlchemy
│   │   │   ├── services/    # Logique métier
│   │   │   ├── solver/      # Moteur OR-Tools
│   │   │   └── ai/          # Agent IA
│   │   ├── alembic/         # Migrations DB
│   │   └── requirements.txt
│   ├── frontend/             # Application React
│   │   ├── src/
│   │   │   ├── components/  # Composants React
│   │   │   ├── pages/       # Pages principales
│   │   │   ├── services/    # Services API
│   │   │   └── store/       # Store Redux
│   │   └── package.json
│   └── scripts/             # Scripts PowerShell
```

## ✅ Fonctionnalités Implémentées

### Core Backend (95% complet)
- ✅ **Modèles de données** complets
- ✅ **Solver OR-Tools** avec contraintes israéliennes
- ✅ **Agent IA** (Claude/GPT) avec parsing de contraintes
- ✅ **Services d'export** (PDF, Excel, ICS)
- ✅ **Authentification JWT** complète
- ✅ **API Schedules** (génération, export, gestion)
- ✅ **API AI** (chat, suggestions, parsing)

### Frontend Core (80% complet)
- ✅ **Pages principales**: Login, Dashboard, Schedule
- ✅ **Composants Schedule**: ScheduleGrid avec drag & drop
- ✅ **Interface IA**: ChatInterface complète
- ✅ **Store Redux**: Auth, Schedule, AI slices
- ✅ **Internationalisation**: Français/Hébreu

## 🔧 Configuration

### Variables d'Environnement (.env)

```bash
# Base de données
DATABASE_URL=sqlite:///./school_timetable.db

# Sécurité
SECRET_KEY=votre-clé-secrète-ici

# Agent IA (optionnel)
USE_CLAUDE=true
ANTHROPIC_API_KEY=votre-clé-anthropic
# OU
OPENAI_API_KEY=votre-clé-openai

# Développement
DEBUG=true
```

### Configuration PostgreSQL (Production)

```bash
# Dans .env
DATABASE_URL=postgresql://user:password@localhost:5432/school_timetable

# Créer les tables
cd backend
alembic upgrade head
```

## 🎯 Spécificités Israéliennes

- **Semaine**: Dimanche à Vendredi
- **Vendredi court**: Fin à 13h
- **Séparation garçons/filles**: Pour certains cours
- **Matières religieuses**: Support spécifique
- **Bilinguisme**: Interface français/hébreu

## 🤖 Agent IA

L'agent IA peut :
- Parser des contraintes en langage naturel
- Expliquer les conflits en termes non-techniques
- Suggérer des améliorations contextuelles
- Supporter le français et l'hébreu

### Configuration IA

```bash
# Pour Claude (Anthropic)
USE_CLAUDE=true
ANTHROPIC_API_KEY=sk-ant-...

# Pour GPT (OpenAI)  
USE_CLAUDE=false
OPENAI_API_KEY=sk-...
```

## 📊 État d'Avancement

| Composant | Avancement | Statut |
|-----------|------------|---------|
| **Modèles DB** | 95% | ✅ Complet |
| **Solver OR-Tools** | 100% | ✅ Complet |
| **Agent IA** | 100% | ✅ Complet |
| **Auth API** | 100% | ✅ Complet |
| **Schedule API** | 100% | ✅ Complet |
| **CRUD APIs** | 20% | 🔴 En cours |
| **Frontend Core** | 80% | ✅ Bon |
| **Pages CRUD** | 10% | 🔴 En cours |

## 🚧 Prochaines Étapes

### Priorité 1: APIs CRUD Backend
- [ ] Teachers API complet
- [ ] Subjects API complet  
- [ ] Classes API complet
- [ ] Rooms API complet

### Priorité 2: Pages Frontend
- [ ] Teachers.tsx (gestion enseignants)
- [ ] Subjects.tsx (gestion matières)
- [ ] Classes.tsx (gestion classes)
- [ ] Rooms.tsx (gestion salles)

## 🐛 Résolution de Problèmes

### Erreur PostgreSQL
```bash
# Solution: Utiliser SQLite pour le développement
DATABASE_URL=sqlite:///./school_timetable.db
```

### Port déjà utilisé
```bash
# Vérifier les ports 3000 et 8000
netstat -ano | findstr :3000
netstat -ano | findstr :8000
```

### Modules manquants
```bash
# Backend
cd backend && pip install -r requirements.txt

# Frontend  
cd frontend && npm install
```

## 📚 Documentation

- **Architecture**: Voir [ARCHITECTURE.md](ARCHITECTURE.md)
- **État d'implémentation**: Voir [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
- **Guide rapide**: Voir [QUICK_START.md](QUICK_START.md)

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -am 'Ajouter nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

🚀 **L'application est maintenant prête pour le développement !**

Utilisez `.\start_with_sqlite.ps1` pour démarrer rapidement. 