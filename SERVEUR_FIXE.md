# 🚀 Serveur School Timetable Generator - RÉPARÉ

## ✅ Problèmes Résolus

Les erreurs suivantes ont été corrigées :

1. **Fichiers `__init__.py` manquants** - Tous les modules Python ont maintenant leurs fichiers `__init__.py`
2. **Imports circulaires** - Les imports `TeacherBasic` et `SubjectBasic` ont été réorganisés
3. **Problèmes de modules** - Le module `app` est maintenant correctement reconnu par Python

## 🏃‍♂️ Démarrage Rapide

### Option 1: Script automatique (Recommandé)
```powershell
# Depuis la racine du projet
.\start_backend_fixed.ps1
```

### Option 2: Démarrage manuel
```powershell
# Aller dans le dossier backend
cd backend

# Configurer la base de données
$env:DATABASE_URL="sqlite:///./school_timetable.db"

# Démarrer le serveur
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 🌐 Endpoints Disponibles

Le serveur est maintenant accessible sur `http://127.0.0.1:8000`

### Endpoints Principaux
- **Documentation Interactive**: http://127.0.0.1:8000/api/v1/docs
- **Health Check**: http://127.0.0.1:8000/health
- **API Root**: http://127.0.0.1:8000/

### API Endpoints (nécessitent authentification)
- **Sujets**: http://127.0.0.1:8000/api/v1/subjects/
- **Enseignants**: http://127.0.0.1:8000/api/v1/teachers/
- **Classes**: http://127.0.0.1:8000/api/v1/class-groups/
- **Salles**: http://127.0.0.1:8000/api/v1/rooms/

## 🔐 Authentification

Un utilisateur de test existe déjà :
- **Username**: `testuser`
- **Password**: `testpass123`

### Obtenir un token d'accès
```powershell
# PowerShell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/auth/login" -Method POST -Headers @{"Content-Type"="application/x-www-form-urlencoded"} -Body "username=testuser&password=testpass123"
```

## 🧪 Test du Serveur

Un script de test est disponible :
```powershell
cd backend
py test_api_simple.py
```

## 📊 Caractéristiques

✅ **24 endpoints API complets** pour la gestion d'emploi du temps  
✅ **Support bilingue** (Français/Hébreu)  
✅ **Base de données SQLite** avec données de test  
✅ **Documentation interactive** avec Swagger UI  
✅ **Authentification JWT** sécurisée  
✅ **Validation des données** avec Pydantic  
✅ **CORS configuré** pour le frontend  

## 🗂️ Structure de l'API

```
/api/v1/
├── auth/           # Authentification
├── subjects/       # Gestion des matières
├── teachers/       # Gestion des enseignants
├── class-groups/   # Gestion des classes
├── rooms/          # Gestion des salles
└── schedules/      # Gestion des emplois du temps
```

## 🔧 Dépannage

### Erreur "Module not found"
Vérifiez que vous êtes dans le dossier `backend` et que tous les fichiers `__init__.py` existent.

### Erreur de port occupé
Changez le port dans la commande uvicorn :
```powershell
py -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### Erreur de base de données
La base de données SQLite sera créée automatiquement au premier démarrage.

## 📝 Logs

Le serveur affiche les logs en temps réel :
- `INFO: Started server process` - Serveur démarré
- `INFO: Application startup complete` - Application prête
- `INFO: Uvicorn running on...` - Serveur accessible

## 🎯 Prochaines Étapes

1. **Frontend** : Le serveur est maintenant prêt pour se connecter au frontend React
2. **Production** : Pour la production, utilisez Gunicorn ou un serveur web approprié
3. **Base de données** : Pour la production, migrez vers PostgreSQL ou MySQL

---

**Status** : ✅ SERVEUR OPÉRATIONNEL  
**Version** : 1.0.0  
**Last Updated** : $(Get-Date -Format "yyyy-MM-dd HH:mm:ss") 