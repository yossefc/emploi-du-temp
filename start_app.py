#!/usr/bin/env python3
"""
Script de démarrage pour l'application School Timetable Generator
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Lance l'application avec les paramètres de développement."""
    
    # Définir les variables d'environnement pour le développement
    os.environ["DATABASE_URL"] = "sqlite:///./school_timetable.db"
    os.environ["SECRET_KEY"] = "dev-secret-key-123"
    os.environ["DEBUG"] = "true"
    os.environ["ANTHROPIC_API_KEY"] = "your-api-key"
    os.environ["OPENAI_API_KEY"] = "your-api-key"
    
    # Naviguer vers le répertoire backend
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    print("🚀 Démarrage de l'application School Timetable Generator...")
    print(f"📁 Répertoire: {backend_dir}")
    print("📊 Base de données: SQLite (développement)")
    print("🌐 API sera disponible sur: http://localhost:8000")
    print("📖 Documentation API: http://localhost:8000/api/v1/docs")
    print()
    
    try:
        # Lancer l'application FastAPI avec uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n✅ Application arrêtée par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 