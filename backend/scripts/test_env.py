#!/usr/bin/env python3
"""
Script pour tester le chargement des variables d'environnement.
"""

import os
import sys
from pathlib import Path

def main():
    print("Test de chargement des variables d'environnement")
    print("=" * 50)
    
    # Répertoire actuel
    current_dir = Path.cwd()
    print(f"Répertoire actuel: {current_dir}")
    
    # Chercher le fichier .env
    env_file = current_dir / ".env"
    if env_file.exists():
        print(f"✅ Fichier .env trouvé: {env_file}")
        
        # Lire le contenu
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chercher DATABASE_URL
        lines = content.split('\n')
        database_urls = []
        for i, line in enumerate(lines, 1):
            if 'DATABASE_URL=' in line and not line.strip().startswith('#'):
                database_urls.append((i, line.strip()))
        
        if database_urls:
            print(f"✅ DATABASE_URL trouvée(s):")
            for line_num, line in database_urls:
                print(f"   Ligne {line_num}: {line}")
        else:
            print("❌ Aucune DATABASE_URL active trouvée")
            print("Lignes contenant DATABASE_URL:")
            for i, line in enumerate(lines, 1):
                if 'DATABASE_URL=' in line:
                    prefix = "   # " if line.strip().startswith('#') else "   > "
                    print(f"{prefix}Ligne {i}: {line.strip()}")
    else:
        print(f"❌ Fichier .env non trouvé: {env_file}")
    
    print("\n" + "=" * 50)
    print("Variables d'environnement actuelles:")
    
    # Vérifier les variables d'environnement
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"✅ DATABASE_URL (env): {database_url}")
    else:
        print("❌ DATABASE_URL non définie dans l'environnement")
    
    # Tester le chargement du module de configuration
    print("\n" + "=" * 50)
    print("Test de chargement de la configuration de l'application:")
    
    try:
        # Ajouter le répertoire parent au path pour importer les modules
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        from app.core.config import settings
        print(f"✅ Configuration chargée")
        print(f"   DATABASE_URL: {settings.DATABASE_URL}")
        
        if 'sqlite:' in settings.DATABASE_URL:
            print("✅ Configuration SQLite détectée")
        elif 'postgresql:' in settings.DATABASE_URL:
            print("⚠️  Configuration PostgreSQL détectée")
        else:
            print(f"❓ Type de base de données non reconnu: {settings.DATABASE_URL}")
            
    except Exception as e:
        print(f"❌ Erreur lors du chargement de la configuration: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main() 