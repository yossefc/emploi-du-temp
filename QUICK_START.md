# 🚀 Guide de Démarrage Rapide

## 📋 Prérequis

- Python 3.8+
- Node.js 14+
- PowerShell (Windows)

## 🔧 Installation

### 1. Backend

```powershell
cd backend
pip install -r requirements.txt
```

### 2. Frontend

```powershell
cd frontend
npm install
```

## 🏃‍♂️ Lancer l'Application

### Option 1: Script PowerShell (Recommandé)

```powershell
.\start_simple.ps1
```

Cela ouvrira deux fenêtres PowerShell :
- Une pour le backend (http://localhost:8000)
- Une pour le frontend (http://localhost:3000)

### Option 2: Manuellement

**Terminal 1 - Backend:**
```powershell
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm start
```

## 🔑 Connexion

1. Ouvrez http://localhost:3000
2. Utilisez les identifiants de test :
   - Email: `admin@example.com`
   - Mot de passe: `password123`

## 📱 Fonctionnalités Implémentées

### ✅ Frontend
- **Pages principales** : Login, Dashboard, Schedule
- **Composants** : ScheduleGrid (drag & drop), ChatInterface (IA), Layout
- **Store Redux** : Auth, Schedule, AI
- **Internationalisation** : Français/Hébreu
- **Authentification JWT** : Login avec token

### ✅ Backend
- **Solver OR-Tools complet** : Génération optimisée d'emplois du temps
- **Agent IA** : Intégration Claude/GPT
- **Services d'export** : PDF, Excel, ICS
- **Tests unitaires** : Structure de base
- **Migrations Alembic** : Gestion de la DB

## 🎯 Navigation

Une fois connecté, vous pouvez :

1. **Dashboard** : Vue d'ensemble avec statistiques
2. **Emploi du temps** : 
   - Cliquer sur "Générer" pour créer un nouvel emploi du temps
   - Utiliser le chat IA (bouton flottant en bas à droite)
   - Exporter en PDF, Excel ou ICS
3. **Autres pages** : En cours de développement

## ⚙️ Configuration de l'Agent IA

Pour activer l'agent IA, ajoutez votre clé API dans le fichier `.env` du backend :

```env
# Pour Claude (Anthropic)
USE_CLAUDE=true
ANTHROPIC_API_KEY=your-api-key-here

# OU pour GPT (OpenAI)
USE_CLAUDE=false
OPENAI_API_KEY=your-api-key-here
```

## 🐛 Résolution de Problèmes

### Erreur PowerShell "&&"
PowerShell ne supporte pas `&&`. Utilisez `;` ou le script `start_simple.ps1`.

### Port déjà utilisé
Vérifiez que les ports 3000 et 8000 sont libres.

### Erreur de module
Assurez-vous d'avoir installé toutes les dépendances :
```powershell
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

## 📚 Documentation

- **API Backend** : http://localhost:8000/api/v1/docs
- **Architecture** : Voir `ARCHITECTURE.md`
- **État de l'implémentation** : Voir `IMPLEMENTATION_STATUS.md`

## 🎉 C'est parti !

L'application est maintenant prête à l'emploi. Explorez les fonctionnalités et n'hésitez pas à contribuer au développement ! 