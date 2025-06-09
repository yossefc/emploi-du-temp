#!/usr/bin/env python3
"""
Script de vérification de la configuration et de l'état de la base de données.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent))

from app.db.base import engine, SessionLocal
from app.core.config import settings


def check_database_connection():
    """Vérifier la connexion à la base de données."""
    print("🔌 Test de connexion à la base de données...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone()[0] == 1:
                print("✅ Connexion réussie")
                return True
    except SQLAlchemyError as e:
        print(f"❌ Erreur de connexion: {e}")
        return False


def check_database_configuration():
    """Vérifier la configuration de la base de données."""
    print("\n⚙️  Configuration de la base de données:")
    print(f"   DATABASE_URL: {settings.DATABASE_URL}")
    print(f"   Type de DB: {'SQLite' if 'sqlite' in settings.DATABASE_URL else 'PostgreSQL'}")
    
    if 'sqlite' in settings.DATABASE_URL:
        db_file = settings.DATABASE_URL.split('///')[-1]
        if db_file.startswith('./'):
            db_path = Path(db_file)
        else:
            db_path = Path(db_file)
        
        print(f"   Fichier DB: {db_path.absolute()}")
        print(f"   Existe: {'✅' if db_path.exists() else '❌'}")
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(f"   Taille: {size_mb:.2f} MB")


def list_tables():
    """Lister toutes les tables dans la base de données."""
    print("\n📋 Tables dans la base de données:")
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if not tables:
            print("   ❌ Aucune table trouvée")
            return []
        
        for i, table in enumerate(tables, 1):
            print(f"   {i:2d}. {table}")
        
        print(f"\n   Total: {len(tables)} table(s)")
        return tables
        
    except SQLAlchemyError as e:
        print(f"   ❌ Erreur: {e}")
        return []


def count_records():
    """Compter les enregistrements dans les tables principales."""
    print("\n📊 Nombre d'enregistrements:")
    
    main_tables = ['users', 'teachers', 'subjects', 'class_groups', 'rooms', 'schedules']
    
    try:
        with SessionLocal() as db:
            for table_name in main_tables:
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    status = "✅" if count > 0 else "🔵"
                    print(f"   {status} {table_name}: {count} enregistrement(s)")
                except SQLAlchemyError:
                    print(f"   ❌ {table_name}: Erreur de lecture")
                    
    except SQLAlchemyError as e:
        print(f"   ❌ Erreur: {e}")


def check_alembic_status():
    """Vérifier l'état des migrations Alembic."""
    print("\n🔄 État des migrations Alembic:")
    
    try:
        inspector = inspect(engine)
        
        if 'alembic_version' not in inspector.get_table_names():
            print("   ❌ Table alembic_version manquante")
            print("   💡 Exécutez: alembic stamp head")
            return
        
        with SessionLocal() as db:
            result = db.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            
            if version:
                print(f"   ✅ Version actuelle: {version}")
                
                # Vérifier s'il y a des migrations en attente
                import subprocess
                try:
                    result = subprocess.run(
                        ["alembic", "current"], 
                        capture_output=True, 
                        text=True,
                        env={**os.environ, "DATABASE_URL": "sqlite:///./school_timetable.db"}
                    )
                    if result.returncode == 0:
                        print(f"   📋 Statut: {result.stdout.strip()}")
                except:
                    pass
            else:
                print("   ❌ Aucune version enregistrée")
                
    except SQLAlchemyError as e:
        print(f"   ❌ Erreur: {e}")


def main():
    """Fonction principale de vérification."""
    print("🏥 VÉRIFICATION DE LA BASE DE DONNÉES")
    print("=" * 50)
    
    # 1. Vérifier la configuration
    check_database_configuration()
    
    # 2. Tester la connexion
    if not check_database_connection():
        print("\n❌ Impossible de continuer sans connexion")
        return False
    
    # 3. Lister les tables
    tables = list_tables()
    if not tables:
        print("\n❌ Aucune table trouvée")
        return False
    
    # 4. Compter les enregistrements
    count_records()
    
    # 5. Vérifier Alembic
    check_alembic_status()
    
    print("\n" + "=" * 50)
    print("🎉 Vérification terminée !")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)
