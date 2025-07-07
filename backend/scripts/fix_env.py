#!/usr/bin/env python3
"""
Script simple pour créer un fichier .env correct avec SQLite.
"""

import secrets
from pathlib import Path
from datetime import datetime

def main():
    # Trouver le répertoire backend
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"Répertoire du projet: {project_root}")
    
    # Créer le fichier .env
    env_file = project_root / ".env"
    
    env_content = f"""# Configuration générée automatiquement le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Security
SECRET_KEY={secrets.token_urlsafe(32)}

# Database (SQLite par défaut - simple et rapide pour débuter)
DATABASE_URL=sqlite:///./school_timetable.db

# Pour PostgreSQL, décommentez et configurez la ligne suivante :
# DATABASE_URL=postgresql://username:password@localhost:5432/school_timetable

# Redis (optionnel, pour les tâches en arrière-plan)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# AI Configuration (optionnel)
USE_CLAUDE=false
ANTHROPIC_API_KEY=your-anthropic-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
AI_MODEL=claude-3-opus-20240229

# Application Settings
DEBUG=true
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Israeli-specific settings
FRIDAY_SHORT_DAY=true
FRIDAY_END_HOUR=13
REGULAR_END_HOUR=16
START_HOUR=8

# Solver settings
SOLVER_TIME_LIMIT_SECONDS=300
SOLVER_NUM_WORKERS=8
"""
    
    # Écrire le fichier
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ Fichier .env créé: {env_file}")
    print("✅ Configuration: SQLite")
    
    # Vérifier que le fichier existe
    if env_file.exists():
        print("✅ Vérification: Fichier présent")
        print("\nContenu du fichier .env:")
        print("-" * 40)
        with open(env_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if i <= 10:  # Afficher les 10 premières lignes
                    print(f"{i:2d}: {line.rstrip()}")
                elif i == 11:
                    print("   ... (contenu tronqué)")
                    break
        print("-" * 40)
    else:
        print("❌ Erreur: Fichier non créé")

if __name__ == "__main__":
    main() 