# Scripts de Configuration

Ce répertoire contient les scripts de configuration automatique pour le backend School Timetable Generator.

## 🚀 Configuration Rapide

### Option 1: Script Python (Recommandé)
```bash
# Depuis le répertoire racine du projet
python backend/scripts/setup.py
```

### Option 2: Script Batch Windows
```cmd
# Double-cliquez sur le fichier ou exécutez depuis cmd
backend\scripts\setup.bat
```

### Option 3: Script PowerShell
```powershell
# Depuis PowerShell
backend\scripts\setup.ps1
```

## 🧹 Nettoyage et Recommencement

Si vous voulez recommencer la configuration depuis zéro :

```bash
# Script de nettoyage (supprime venv, .env, base de données, etc.)
python backend/scripts/clean_setup.py

# Puis relancez la configuration
python backend/scripts/setup.py
```

## 📋 Ce que fait le script

Le script `setup.py` effectue automatiquement les tâches suivantes :

1. **Vérification de l'environnement Python** (>= 3.11)
2. **Création de l'environnement virtuel** (`backend/venv/`)
3. **Installation des dépendances** (depuis `requirements.txt`)
4. **Configuration de l'environnement** (création du fichier `.env`)
5. **Création de la base de données** (SQLite par défaut)
6. **Exécution des migrations** (Alembic)
7. **Création de l'utilisateur admin**
8. **Chargement des données de test**
9. **Affichage des instructions de démarrage**

## 🔧 Caractéristiques

- **Idempotent** : Peut être exécuté plusieurs fois sans problème
- **Gestion d'erreurs** : Arrêt propre en cas d'erreur
- **Couleurs** : Affichage coloré pour une meilleure lisibilité
- **Cross-platform** : Compatible Windows, macOS, Linux
- **Détection automatique** : Détecte les composants déjà installés

## 📁 Fichiers créés

Après exécution, le script crée/configure :

```
backend/
├── venv/                    # Environnement virtuel Python
├── .env                     # Variables d'environnement
├── school_timetable.db      # Base de données SQLite
└── logs/                    # Répertoire des logs (si créé)
```

## 👤 Utilisateur Admin

Le script crée automatiquement un utilisateur administrateur :

- **Email** : `admin@school.edu.il`
- **Mot de passe** : `admin123`
- **Rôle** : Administrateur

⚠️ **Changez ce mot de passe en production !**

## 🛠️ Dépannage

### Erreur de base de données PostgreSQL
Si vous voyez une erreur comme "could not translate host name 'postgres'":

```bash
# Option 1: Utiliser le script de nettoyage et recommencer avec SQLite
python backend/scripts/clean_setup.py
python backend/scripts/setup.py

# Option 2: Configurer PostgreSQL correctement
# Installez PostgreSQL, créez une base de données, puis modifiez .env
```

### Python non trouvé
```bash
# Vérifiez que Python est installé
python --version
python3 --version

# Ou installez Python 3.11+
# https://www.python.org/downloads/
```

### Erreur de permissions
```bash
# Sur Linux/macOS, rendez le script exécutable
chmod +x backend/scripts/setup.py

# Ou exécutez avec python
python backend/scripts/setup.py
```

### Problème avec pip
```bash
# Mettez à jour pip
python -m pip install --upgrade pip

# Ou utilisez pip3
python3 -m pip install --upgrade pip
```

### Recommencer la configuration
```bash
# Utilisez le script de nettoyage pour tout supprimer et recommencer
python backend/scripts/clean_setup.py
python backend/scripts/setup.py
```

## 🔄 Réexécution

Le script peut être réexécuté à tout moment :

- Les composants existants sont détectés et conservés
- Seuls les éléments manquants sont créés
- Les données existantes ne sont pas écrasées

## 📞 Support

En cas de problème :

1. Vérifiez les prérequis (Python 3.11+)
2. Consultez les logs d'erreur affichés
3. Relancez le script après correction
4. Consultez la documentation du projet

## 🔧 Configuration Avancée

### PostgreSQL
Pour utiliser PostgreSQL au lieu de SQLite :

1. Installez PostgreSQL
2. Modifiez `DATABASE_URL` dans `.env` :
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/school_timetable
   ```

### Intelligence Artificielle
Pour activer l'IA :

1. Obtenez une clé API (Anthropic ou OpenAI)
2. Ajoutez-la dans `.env` :
   ```
   ANTHROPIC_API_KEY=your-key-here
   # ou
   OPENAI_API_KEY=your-key-here
   ```

### Redis
Pour les tâches en arrière-plan :

1. Installez Redis
2. Vérifiez `REDIS_URL` dans `.env`
3. Démarrez Redis : `redis-server` 