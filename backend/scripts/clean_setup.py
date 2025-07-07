#!/usr/bin/env python3
"""
Script de nettoyage pour recommencer la configuration du backend.

Ce script supprime :
- L'environnement virtuel
- Le fichier .env
- La base de données SQLite
- Les fichiers temporaires

Utile pour recommencer une configuration propre.
"""

import os
import sys
import shutil
from pathlib import Path

# Configuration des couleurs ANSI
class Colors:
    """Codes couleur ANSI pour l'affichage en terminal."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message: str, color: str = Colors.ENDC, bold: bool = False):
    """Affiche un message avec des couleurs."""
    prefix = Colors.BOLD if bold else ""
    print(f"{prefix}{color}{message}{Colors.ENDC}")

def print_header(message: str):
    """Affiche un en-tête coloré."""
    print_colored(f"\n{'='*60}", Colors.HEADER, bold=True)
    print_colored(f"  {message}", Colors.HEADER, bold=True)
    print_colored(f"{'='*60}", Colors.HEADER, bold=True)

def print_success(message: str):
    """Affiche un message de succès."""
    print_colored(f"✅ {message}", Colors.OKGREEN)

def print_warning(message: str):
    """Affiche un avertissement."""
    print_colored(f"⚠️  {message}", Colors.WARNING)

def print_error(message: str):
    """Affiche une erreur."""
    print_colored(f"❌ {message}", Colors.FAIL)

def print_info(message: str):
    """Affiche une information."""
    print_colored(f"ℹ️  {message}", Colors.OKCYAN)

def get_project_root() -> Path:
    """Trouve le répertoire racine du projet."""
    current_dir = Path(__file__).parent
    # Remonte jusqu'à trouver le répertoire backend
    while current_dir.name != "backend" and current_dir.parent != current_dir:
        current_dir = current_dir.parent
    return current_dir

def confirm_action(message: str) -> bool:
    """Demande confirmation à l'utilisateur."""
    while True:
        response = input(f"{message} (o/n): ").lower().strip()
        if response in ['o', 'oui', 'y', 'yes']:
            return True
        elif response in ['n', 'non', 'no']:
            return False
        else:
            print_warning("Répondez par 'o' (oui) ou 'n' (non)")

def clean_virtual_environment(project_root: Path) -> bool:
    """Supprime l'environnement virtuel."""
    venv_path = project_root / "venv"
    
    if not venv_path.exists():
        print_info("Environnement virtuel non trouvé")
        return True
    
    if not confirm_action("Supprimer l'environnement virtuel ?"):
        print_info("Environnement virtuel conservé")
        return True
    
    try:
        shutil.rmtree(venv_path)
        print_success("Environnement virtuel supprimé")
        return True
    except Exception as e:
        print_error(f"Erreur lors de la suppression de l'environnement virtuel: {e}")
        return False

def clean_env_file(project_root: Path) -> bool:
    """Supprime le fichier .env."""
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print_info("Fichier .env non trouvé")
        return True
    
    if not confirm_action("Supprimer le fichier .env ?"):
        print_info("Fichier .env conservé")
        return True
    
    try:
        env_file.unlink()
        print_success("Fichier .env supprimé")
        return True
    except Exception as e:
        print_error(f"Erreur lors de la suppression du fichier .env: {e}")
        return False

def clean_database(project_root: Path) -> bool:
    """Supprime la base de données SQLite."""
    db_files = [
        project_root / "school_timetable.db",
        project_root / "school_timetable.db-journal",
        project_root / "school_timetable.db-wal",
        project_root / "school_timetable.db-shm"
    ]
    
    existing_files = [f for f in db_files if f.exists()]
    
    if not existing_files:
        print_info("Base de données SQLite non trouvée")
        return True
    
    if not confirm_action("Supprimer la base de données SQLite ?"):
        print_info("Base de données conservée")
        return True
    
    try:
        for db_file in existing_files:
            db_file.unlink()
            print_success(f"Fichier {db_file.name} supprimé")
        return True
    except Exception as e:
        print_error(f"Erreur lors de la suppression de la base de données: {e}")
        return False

def clean_temp_files(project_root: Path) -> bool:
    """Supprime les fichiers temporaires."""
    temp_patterns = [
        "temp_*.py",
        "*.pyc",
        "__pycache__",
        "*.log"
    ]
    
    print_info("Nettoyage des fichiers temporaires...")
    
    try:
        # Supprimer les fichiers temporaires dans le répertoire racine
        for pattern in temp_patterns:
            if pattern == "__pycache__":
                for pycache_dir in project_root.rglob("__pycache__"):
                    shutil.rmtree(pycache_dir)
                    print_success(f"Répertoire {pycache_dir.relative_to(project_root)} supprimé")
            else:
                for file in project_root.glob(pattern):
                    file.unlink()
                    print_success(f"Fichier {file.name} supprimé")
        
        return True
    except Exception as e:
        print_error(f"Erreur lors du nettoyage des fichiers temporaires: {e}")
        return False

def clean_logs(project_root: Path) -> bool:
    """Supprime les logs."""
    logs_dir = project_root / "logs"
    
    if not logs_dir.exists():
        print_info("Répertoire logs non trouvé")
        return True
    
    if not confirm_action("Supprimer les logs ?"):
        print_info("Logs conservés")
        return True
    
    try:
        shutil.rmtree(logs_dir)
        print_success("Répertoire logs supprimé")
        return True
    except Exception as e:
        print_error(f"Erreur lors de la suppression des logs: {e}")
        return False

def main():
    """Fonction principale du script de nettoyage."""
    print_header("🧹 NETTOYAGE DE LA CONFIGURATION")
    print_colored("Script de nettoyage pour recommencer la configuration", Colors.OKCYAN)
    
    try:
        # Trouve le répertoire du projet
        project_root = get_project_root()
        print_info(f"Répertoire du projet: {project_root}")
        
        print_warning("\nATTENTION: Cette opération va supprimer des fichiers!")
        print_warning("Assurez-vous d'avoir sauvegardé vos données importantes.")
        
        if not confirm_action("\nContinuer le nettoyage ?"):
            print_info("Nettoyage annulé")
            return 0
        
        # Nettoyage étape par étape
        print_colored("\n🧹 Début du nettoyage...", Colors.OKBLUE, bold=True)
        
        success = True
        
        # Étape 1: Environnement virtuel
        success &= clean_virtual_environment(project_root)
        
        # Étape 2: Fichier .env
        success &= clean_env_file(project_root)
        
        # Étape 3: Base de données
        success &= clean_database(project_root)
        
        # Étape 4: Fichiers temporaires
        success &= clean_temp_files(project_root)
        
        # Étape 5: Logs
        success &= clean_logs(project_root)
        
        if success:
            print_colored("\n🎉 Nettoyage terminé avec succès!", Colors.OKGREEN, bold=True)
            print_info("Vous pouvez maintenant relancer le script de configuration:")
            print_colored("python backend/scripts/setup.py", Colors.OKCYAN)
        else:
            print_colored("\n⚠️  Nettoyage terminé avec des erreurs", Colors.WARNING, bold=True)
            print_info("Certains fichiers n'ont pas pu être supprimés")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print_error("\nNettoyage interrompu par l'utilisateur")
        return 1
    except Exception as e:
        print_error(f"Erreur inattendue: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 