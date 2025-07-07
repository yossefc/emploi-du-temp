#!/usr/bin/env python3
"""
Script de configuration automatique pour le backend School Timetable Generator.

Ce script :
1. Vérifie l'environnement Python (>= 3.11)
2. Crée l'environnement virtuel
3. Installe les dépendances
4. Crée la base de données
5. Exécute les migrations
6. Crée un utilisateur admin
7. Charge des données de test
8. Affiche les instructions de démarrage

Le script est idempotent et gère les erreurs avec des couleurs pour la lisibilité.
"""

import os
import sys
import subprocess
import platform
import secrets
from pathlib import Path
from typing import Optional, Tuple
import sqlite3
from datetime import datetime

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
    UNDERLINE = '\033[4m'

def print_colored(message: str, color: str = Colors.ENDC, bold: bool = False):
    """Affiche un message avec des couleurs."""
    prefix = Colors.BOLD if bold else ""
    print(f"{prefix}{color}{message}{Colors.ENDC}")

def print_header(message: str):
    """Affiche un en-tête coloré."""
    print_colored(f"\n{'='*60}", Colors.HEADER, bold=True)
    print_colored(f"  {message}", Colors.HEADER, bold=True)
    print_colored(f"{'='*60}", Colors.HEADER, bold=True)

def print_step(step_num: int, message: str):
    """Affiche une étape numérotée."""
    print_colored(f"\n[{step_num}] {message}", Colors.OKBLUE, bold=True)

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

def run_command(command: str, cwd: Optional[str] = None, check: bool = True) -> Tuple[bool, str]:
    """Exécute une commande et retourne le résultat."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()

def check_python_version() -> bool:
    """Vérifie que Python >= 3.11 est installé."""
    print_step(1, "Vérification de la version Python")
    
    version = sys.version_info
    print_info(f"Version Python détectée: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print_error("Python 3.11 ou supérieur est requis")
        print_info("Veuillez installer Python 3.11+ depuis https://www.python.org/downloads/")
        return False
    
    print_success("Version Python compatible")
    return True

def get_project_root() -> Path:
    """Trouve le répertoire racine du projet."""
    current_dir = Path(__file__).parent
    # Remonte jusqu'à trouver le répertoire backend
    while current_dir.name != "backend" and current_dir.parent != current_dir:
        current_dir = current_dir.parent
    return current_dir

def create_virtual_environment(project_root: Path) -> bool:
    """Crée l'environnement virtuel s'il n'existe pas."""
    print_step(2, "Configuration de l'environnement virtuel")
    
    venv_path = project_root / "venv"
    
    if venv_path.exists():
        print_warning("L'environnement virtuel existe déjà")
        return True
    
    print_info("Création de l'environnement virtuel...")
    success, output = run_command(f'python -m venv "{venv_path}"', str(project_root))
    
    if not success:
        print_error(f"Échec de la création de l'environnement virtuel: {output}")
        return False
    
    print_success("Environnement virtuel créé avec succès")
    return True

def get_venv_python(project_root: Path) -> str:
    """Retourne le chemin vers l'exécutable Python de l'environnement virtuel."""
    if platform.system() == "Windows":
        return str(project_root / "venv" / "Scripts" / "python.exe")
    else:
        return str(project_root / "venv" / "bin" / "python")

def get_venv_pip(project_root: Path) -> str:
    """Retourne le chemin vers pip de l'environnement virtuel."""
    if platform.system() == "Windows":
        return str(project_root / "venv" / "Scripts" / "pip.exe")
    else:
        return str(project_root / "venv" / "bin" / "pip")

def install_dependencies(project_root: Path) -> bool:
    """Installe les dépendances Python."""
    print_step(3, "Installation des dépendances")
    
    requirements_file = project_root / "requirements.txt"
    if not requirements_file.exists():
        print_error("Fichier requirements.txt non trouvé")
        return False
    
    pip_path = get_venv_pip(project_root)
    
    print_info("Mise à jour de pip...")
    success, output = run_command(f'"{pip_path}" install --upgrade pip', str(project_root))
    if not success:
        print_warning(f"Avertissement lors de la mise à jour de pip: {output}")
    
    print_info("Installation des dépendances...")
    success, output = run_command(f'"{pip_path}" install -r requirements.txt', str(project_root))
    
    if not success:
        print_error(f"Échec de l'installation des dépendances: {output}")
        return False
    
    print_success("Dépendances installées avec succès")
    return True

def create_env_file(project_root: Path) -> bool:
    """Crée le fichier .env s'il n'existe pas."""
    print_step(4, "Configuration du fichier d'environnement")
    
    env_file = project_root / ".env"
    env_example = project_root.parent / "env.example"
    
    if env_file.exists():
        print_warning("Le fichier .env existe déjà")
        # Vérifier si c'est une configuration PostgreSQL problématique et la corriger
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'DATABASE_URL=postgresql:' in content and 'postgres' in content:
                    print_warning("Configuration PostgreSQL problématique détectée")
                    print_info("Conversion automatique vers SQLite...")
                    
                    # Remplacer la ligne PostgreSQL par SQLite
                    lines = content.split('\n')
                    new_lines = []
                    for line in lines:
                        if line.strip().startswith('DATABASE_URL=postgresql:'):
                            new_lines.append('# Configuration PostgreSQL originale (commentée)')
                            new_lines.append(f'# {line}')
                            new_lines.append('')
                            new_lines.append('# Configuration SQLite (active)')
                            new_lines.append('DATABASE_URL=sqlite:///./school_timetable.db')
                        else:
                            new_lines.append(line)
                    
                    # Réécrire le fichier
                    with open(env_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(new_lines))
                    
                    print_success("Configuration convertie vers SQLite")
                    return True
                else:
                    print_info("Configuration existante conservée")
        except Exception as e:
            print_warning(f"Erreur lors de la vérification du .env: {e}")
        return True
    
    # Créer un nouveau fichier .env
    print_info("Création d'un nouveau fichier .env")
    
    # Essayer de partir de env.example s'il existe
    env_content = None
    if env_example.exists():
        print_info("Utilisation de env.example comme base")
        try:
            with open(env_example, 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            # Remplace la clé secrète par une vraie clé générée
            if "SECRET_KEY=your-secret-key-here-change-in-production" in env_content:
                env_content = env_content.replace(
                    "SECRET_KEY=your-secret-key-here-change-in-production",
                    f"SECRET_KEY={secrets.token_urlsafe(32)}"
                )
            
            # Utilise SQLite par défaut avec commentaire explicatif
            if "DATABASE_URL=postgresql://postgres:password@localhost:5432/school_timetable" in env_content:
                env_content = env_content.replace(
                    "DATABASE_URL=postgresql://postgres:password@localhost:5432/school_timetable",
                    """# Database (SQLite par défaut - simple et rapide pour débuter)
DATABASE_URL=sqlite:///./school_timetable.db

# Pour PostgreSQL, décommentez et configurez la ligne suivante :
# DATABASE_URL=postgresql://username:password@localhost:5432/school_timetable"""
                )
            
        except Exception as e:
            print_warning(f"Erreur lors de la lecture de env.example: {e}")
            env_content = None
    
    # Si on n'a pas pu utiliser env.example, créer un contenu par défaut
    if env_content is None:
        print_info("Création d'une configuration par défaut")
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
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print_success("Fichier .env créé avec succès")
        print_info(f"Fichier créé: {env_file}")
        print_info("Configuration par défaut: SQLite (recommandé pour débuter)")
        
        # Vérifier que le fichier a bien été créé
        if env_file.exists():
            print_success("Vérification: Fichier .env présent")
        else:
            print_error("Erreur: Fichier .env non créé")
            return False
            
        return True
    except Exception as e:
        print_error(f"Erreur lors de la création du fichier .env: {e}")
        return False

def setup_database(project_root: Path) -> bool:
    """Configure la base de données."""
    print_step(5, "Configuration de la base de données")
    
    python_path = get_venv_python(project_root)
    
    # Vérifie si la base de données existe déjà
    db_file = project_root / "school_timetable.db"
    if db_file.exists():
        print_warning("La base de données existe déjà")
        
        # Vérifie si elle contient des tables
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            if tables:
                print_info(f"Base de données contient {len(tables)} table(s)")
                return True
        except Exception as e:
            print_warning(f"Erreur lors de la vérification de la base de données: {e}")
    
    print_info("Création des tables de base de données...")
    
    # Crée les tables via l'application
    create_tables_script = f"""
import sys
sys.path.insert(0, '{project_root}')

from app.db.base import Base, engine
from app.core.config import settings
import app.models  # Import tous les modèles

try:
    Base.metadata.create_all(bind=engine)
    print("Tables créées avec succès")
except Exception as e:
    print(f"Erreur lors de la création des tables: {{e}}")
    sys.exit(1)
"""
    
    # Écrit le script temporaire
    temp_script = project_root / "temp_create_tables.py"
    with open(temp_script, 'w', encoding='utf-8') as f:
        f.write(create_tables_script)
    
    try:
        success, output = run_command(f'"{python_path}" temp_create_tables.py', str(project_root))
        if not success:
            print_error(f"Échec de la création des tables: {output}")
            return False
        
        print_success("Base de données configurée avec succès")
        return True
    finally:
        # Supprime le script temporaire
        if temp_script.exists():
            temp_script.unlink()

def run_migrations(project_root: Path) -> bool:
    """Exécute les migrations Alembic."""
    print_step(6, "Exécution des migrations")
    
    python_path = get_venv_python(project_root)
    
    # Vérifie si Alembic est configuré
    alembic_ini = project_root / "alembic.ini"
    if not alembic_ini.exists():
        print_warning("Fichier alembic.ini non trouvé, migrations ignorées")
        return True
    
    # Vérifie si le fichier .env existe et contient DATABASE_URL
    env_file = project_root / ".env"
    if env_file.exists():
        print_info("Vérification de la configuration de base de données...")
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.read()
                if 'DATABASE_URL=sqlite:' in env_content:
                    print_info("Configuration SQLite détectée")
                elif 'DATABASE_URL=postgresql:' in env_content:
                    print_info("Configuration PostgreSQL détectée")
                    # Vérifier si PostgreSQL est accessible
                    if not check_postgresql_connection(env_content):
                        print_warning("PostgreSQL non accessible, migration ignorée")
                        print_info("Conseil: Utilisez SQLite pour un démarrage rapide")
                        return True
        except Exception as e:
            print_warning(f"Erreur lors de la lecture du fichier .env: {e}")
    
    print_info("Exécution des migrations Alembic...")
    
    # Définir la variable d'environnement pour s'assurer que le bon DATABASE_URL est utilisé
    env_vars = os.environ.copy()
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        except Exception as e:
            print_warning(f"Erreur lors du chargement des variables d'environnement: {e}")
    
    # Exécuter la commande avec les variables d'environnement
    try:
        result = subprocess.run(
            f'"{python_path}" -m alembic upgrade head',
            shell=True,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            env=env_vars,
            check=False
        )
        
        if result.returncode != 0:
            error_output = result.stderr.strip()
            if "No such file or directory" in error_output or "cannot find" in error_output.lower():
                print_warning("Alembic non installé, migrations ignorées")
                return True
            elif "could not translate host name" in error_output or "Connection refused" in error_output:
                print_warning("Base de données non accessible, migrations ignorées")
                print_info("Conseil: Vérifiez que votre base de données est démarrée ou utilisez SQLite")
                return True
            else:
                print_error(f"Échec des migrations: {error_output}")
                return False
        
        print_success("Migrations exécutées avec succès")
        return True
        
    except Exception as e:
        print_error(f"Erreur lors de l'exécution des migrations: {e}")
        return False

def check_postgresql_connection(env_content: str) -> bool:
    """Vérifie si PostgreSQL est accessible."""
    try:
        import re
        # Extraire l'URL de la base de données
        match = re.search(r'DATABASE_URL=(.+)', env_content)
        if not match:
            return False
        
        db_url = match.group(1).strip()
        if not db_url.startswith('postgresql:'):
            return True  # Pas PostgreSQL, donc pas besoin de vérifier
        
        # Essayer de se connecter
        import psycopg2
        from urllib.parse import urlparse
        
        parsed = urlparse(db_url)
        conn = psycopg2.connect(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/') if parsed.path else 'postgres',
            user=parsed.username or 'postgres',
            password=parsed.password or '',
            connect_timeout=5
        )
        conn.close()
        return True
    except Exception:
        return False

def create_admin_user(project_root: Path) -> bool:
    """Crée un utilisateur administrateur."""
    print_step(7, "Création de l'utilisateur administrateur")
    
    python_path = get_venv_python(project_root)
    
    create_admin_script = f"""
import sys
sys.path.insert(0, '{project_root}')

from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.models.user import User, UserRole
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    db = SessionLocal()
    try:
        # Vérifie si l'admin existe déjà
        existing_admin = db.query(User).filter(User.email == "admin@school.edu.il").first()
        if existing_admin:
            print("Utilisateur admin existe déjà")
            return
        
        # Crée l'utilisateur admin
        admin_user = User(
            email="admin@school.edu.il",
            username="admin",
            full_name="Administrateur Système",
            hashed_password=pwd_context.hash("admin123"),
            role=UserRole.ADMIN,
            language_preference="fr",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        print("Utilisateur admin créé avec succès")
        print("Email: admin@school.edu.il")
        print("Mot de passe: admin123")
        
    except Exception as e:
        print(f"Erreur lors de la création de l'admin: {{e}}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
"""
    
    # Écrit le script temporaire
    temp_script = project_root / "temp_create_admin.py"
    with open(temp_script, 'w', encoding='utf-8') as f:
        f.write(create_admin_script)
    
    try:
        success, output = run_command(f'"{python_path}" temp_create_admin.py', str(project_root))
        if not success:
            print_error(f"Échec de la création de l'admin: {output}")
            return False
        
        print_success("Utilisateur administrateur configuré")
        print_info("Email: admin@school.edu.il")
        print_info("Mot de passe: admin123")
        return True
    finally:
        # Supprime le script temporaire
        if temp_script.exists():
            temp_script.unlink()

def load_test_data(project_root: Path) -> bool:
    """Charge les données de test."""
    print_step(8, "Chargement des données de test")
    
    python_path = get_venv_python(project_root)
    
    # Vérifie si le fichier init_data.py existe
    init_data_file = project_root / "app" / "db" / "init_data.py"
    if not init_data_file.exists():
        print_warning("Fichier init_data.py non trouvé, données de test ignorées")
        return True
    
    load_data_script = f"""
import sys
sys.path.insert(0, '{project_root}')

from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.init_data import populate_test_data

def load_data():
    db = SessionLocal()
    try:
        result = populate_test_data(db)
        print("Données de test chargées avec succès:")
        for key, value in result.items():
            if isinstance(value, list):
                print(f"  - {{key}}: {{len(value)}} éléments")
            else:
                print(f"  - {{key}}: {{value}}")
    except Exception as e:
        print(f"Erreur lors du chargement des données: {{e}}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_data()
"""
    
    # Écrit le script temporaire
    temp_script = project_root / "temp_load_data.py"
    with open(temp_script, 'w', encoding='utf-8') as f:
        f.write(load_data_script)
    
    try:
        success, output = run_command(f'"{python_path}" temp_load_data.py', str(project_root))
        if not success:
            print_warning(f"Avertissement lors du chargement des données: {output}")
            return True  # Continue même si les données de test échouent
        
        print_success("Données de test chargées avec succès")
        return True
    finally:
        # Supprime le script temporaire
        if temp_script.exists():
            temp_script.unlink()

def show_startup_instructions(project_root: Path):
    """Affiche les instructions de démarrage."""
    print_header("🚀 CONFIGURATION TERMINÉE AVEC SUCCÈS!")
    
    print_colored("\n📋 Instructions de démarrage:", Colors.OKBLUE, bold=True)
    
    venv_activate = "venv\\Scripts\\activate" if platform.system() == "Windows" else "source venv/bin/activate"
    
    print_colored(f"""
1. Activez l'environnement virtuel:
   cd {project_root}
   {venv_activate}

2. Démarrez le serveur de développement:
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

3. Accédez à l'application:
   • API: http://localhost:8000
   • Documentation: http://localhost:8000/docs
   • Santé: http://localhost:8000/health

4. Connexion administrateur:
   • Email: admin@school.edu.il
   • Mot de passe: admin123

5. Fichiers importants:
   • Configuration: .env
   • Base de données: school_timetable.db
   • Logs: logs/

6. Commandes utiles:
   • Tests: python -m pytest
   • Migrations: python -m alembic upgrade head
   • Shell interactif: python -c "from app.db.base import SessionLocal; db = SessionLocal()"
""", Colors.OKCYAN)
    
    print_colored("\n🔧 Configuration avancée:", Colors.WARNING, bold=True)
    print_colored("""
• Pour utiliser PostgreSQL: modifiez DATABASE_URL dans .env
• Pour l'IA: ajoutez ANTHROPIC_API_KEY ou OPENAI_API_KEY dans .env
• Pour Redis: installez Redis et vérifiez REDIS_URL dans .env
• Pour la production: définissez DEBUG=false dans .env
""", Colors.WARNING)
    
    print_colored(f"\n✨ Projet configuré dans: {project_root}", Colors.OKGREEN, bold=True)

def main():
    """Fonction principale du script de configuration."""
    print_header("🏫 SCHOOL TIMETABLE GENERATOR - CONFIGURATION")
    print_colored("Script de configuration automatique", Colors.OKCYAN)
    
    try:
        # Étape 1: Vérification Python
        if not check_python_version():
            return 1
        
        # Trouve le répertoire du projet
        project_root = get_project_root()
        print_info(f"Répertoire du projet: {project_root}")
        
        # Étape 2: Environnement virtuel
        if not create_virtual_environment(project_root):
            return 1
        
        # Étape 3: Installation des dépendances
        if not install_dependencies(project_root):
            return 1
        
        # Étape 4: Configuration de l'environnement
        if not create_env_file(project_root):
            return 1
        
        # Étape 5: Base de données
        if not setup_database(project_root):
            return 1
        
        # Étape 6: Migrations
        if not run_migrations(project_root):
            return 1
        
        # Étape 7: Utilisateur admin
        if not create_admin_user(project_root):
            return 1
        
        # Étape 8: Données de test
        if not load_test_data(project_root):
            print_warning("Données de test non chargées, mais le projet est fonctionnel")
        
        # Instructions finales
        show_startup_instructions(project_root)
        
        return 0
        
    except KeyboardInterrupt:
        print_error("\nConfiguration interrompue par l'utilisateur")
        return 1
    except Exception as e:
        print_error(f"Erreur inattendue: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 