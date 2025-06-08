# Guide de Démarrage Simple - Générateur d'Emplois du Temps

## Démarrage Manuel (Recommandé)

### 1. Backend (Terminal 1)
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend (Terminal 2)
```bash
cd frontend
$env:PORT="3001"
yarn start
```

## Accès à l'Application

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **Documentation API**: http://localhost:8000/docs

## Connexion

- **Email**: admin@example.com
- **Mot de passe**: password123

## État des Corrections

✅ **Backend**: Toutes les erreurs corrigées
- Configuration Pydantic (validation boolean avec commentaires)
- Imports manquants corrigés
- Base de données SQLite configurée

✅ **Frontend**: Conversion Redux → React Context
- Suppression de Redux Toolkit et react-redux
- Remplacement par React Context API
- Tous les composants mis à jour

✅ **Dépendances**: Nettoyage complet
- node_modules et yarn.lock supprimés et réinstallés
- Cache yarn nettoyé
- react-beautiful-dnd retiré (incompatible React 18)

## Structure de l'Application

### Backend (Python/FastAPI)
- **Port**: 8000
- **Base de données**: SQLite (./backend/school_timetable.db)
- **API REST**: CRUD complet pour les emplois du temps
- **IA**: Intégration Claude/OpenAI (optionnelle)

### Frontend (React/TypeScript)
- **Port**: 3001
- **État**: React Context (plus Redux)
- **UI**: Material-UI
- **Fonctionnalités**: Génération, édition, export des emplois du temps

## Résolution des Problèmes

### Si le port 3001 est occupé
```bash
$env:PORT="3002"
yarn start
```

### Si erreurs de dépendances
```bash
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item yarn.lock
yarn install
```

### Si erreurs backend
Vérifier que le fichier `.env` existe dans `/backend` avec :
```
DATABASE_URL=sqlite:///./school_timetable.db
SECRET_KEY=dev-secret-key-123
DEBUG=true
``` 