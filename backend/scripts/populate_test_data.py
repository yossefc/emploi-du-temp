#!/usr/bin/env python3
"""
Script pour peupler la base de données avec des données de test réalistes
pour l'application de génération d'emplois du temps scolaires israéliens.
"""

import sys
import os
from pathlib import Path
import argparse
from typing import Optional

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.base import SessionLocal, engine
from app.db.init_data import populate_test_data, clear_all_data
from app.core.config import settings


def get_db_session() -> Session:
    """Obtenir une session de base de données."""
    return SessionLocal()


def check_database_connection():
    """Vérifier la connexion à la base de données."""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return False


def show_current_data_stats(db: Session):
    """Afficher les statistiques actuelles des données."""
    from sqlalchemy import text
    
    print("\n📊 État actuel de la base de données:")
    
    tables = [
        ("users", "Utilisateurs"),
        ("teachers", "Enseignants"), 
        ("subjects", "Matières"),
        ("class_groups", "Classes"),
        ("rooms", "Salles"),
        ("teacher_subjects", "Associations enseignants-matières"),
        ("teacher_availabilities", "Disponibilités"),
        ("class_subject_requirements", "Exigences par classe"),
        ("global_constraints", "Contraintes globales")
    ]
    
    for table_name, display_name in tables:
        try:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            status = "✅" if count > 0 else "🔵"
            print(f"   {status} {display_name}: {count}")
        except Exception as e:
            print(f"   ❌ {display_name}: Erreur ({e})")


def confirm_action(action: str) -> bool:
    """Demander confirmation pour une action."""
    response = input(f"\n⚠️  Êtes-vous sûr de vouloir {action} ? (oui/non): ").lower().strip()
    return response in ["oui", "o", "yes", "y"]


def populate_data_interactive(db: Session):
    """Peupler les données en mode interactif."""
    print("🏫 PEUPLEMENT DES DONNÉES DE TEST")
    print("=" * 50)
    
    # Afficher l'état actuel
    show_current_data_stats(db)
    
    # Demander confirmation
    if not confirm_action("créer les données de test"):
        print("❌ Opération annulée")
        return False
    
    try:
        # Peupler les données
        print("\n🚀 Début du peuplement...")
        stats = populate_test_data(db)
        
        print("\n" + "=" * 50)
        print("✅ DONNÉES DE TEST CRÉÉES AVEC SUCCÈS !")
        print("\n📈 Résumé:")
        for key, value in stats.items():
            print(f"   • {key.replace('_', ' ').title()}: {value}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du peuplement: {e}")
        db.rollback()
        return False


def clear_data_interactive(db: Session):
    """Vider les données en mode interactif."""
    print("🧹 SUPPRESSION DE TOUTES LES DONNÉES")
    print("=" * 50)
    
    # Afficher l'état actuel
    show_current_data_stats(db)
    
    # Double confirmation pour la suppression
    if not confirm_action("SUPPRIMER TOUTES LES DONNÉES"):
        print("❌ Opération annulée")
        return False
    
    print("\n⚠️  ATTENTION: Cette action est IRRÉVERSIBLE!")
    if not confirm_action("continuer la suppression"):
        print("❌ Opération annulée")
        return False
    
    try:
        # Vider les données
        print("\n🗑️  Suppression en cours...")
        clear_all_data(db)
        
        print("✅ Toutes les données ont été supprimées !")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la suppression: {e}")
        db.rollback()
        return False


def reset_and_populate(db: Session):
    """Vider et repeupler les données."""
    print("🔄 RÉINITIALISATION COMPLÈTE")
    print("=" * 50)
    
    # Afficher l'état actuel
    show_current_data_stats(db)
    
    # Demander confirmation
    if not confirm_action("réinitialiser complètement la base de données"):
        print("❌ Opération annulée")
        return False
    
    try:
        # 1. Vider les données
        print("\n🧹 Suppression des données existantes...")
        clear_all_data(db)
        
        # 2. Peupler avec de nouvelles données
        print("\n🏗️  Création des nouvelles données...")
        stats = populate_test_data(db)
        
        print("\n" + "=" * 50)
        print("✅ RÉINITIALISATION TERMINÉE !")
        print("\n📈 Nouvelles données:")
        for key, value in stats.items():
            print(f"   • {key.replace('_', ' ').title()}: {value}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la réinitialisation: {e}")
        db.rollback()
        return False


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Gestionnaire de données de test pour l'école israélienne"
    )
    parser.add_argument(
        "action",
        choices=["populate", "clear", "reset", "stats"],
        help="Action à effectuer"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forcer l'action sans demander confirmation"
    )
    
    args = parser.parse_args()
    
    # Vérifier la connexion
    print("🔍 Vérification de la connexion à la base de données...")
    print(f"   Database URL: {settings.DATABASE_URL}")
    
    if not check_database_connection():
        sys.exit(1)
    
    print("✅ Connexion réussie !")
    
    # Obtenir une session
    db = get_db_session()
    
    try:
        if args.action == "stats":
            # Afficher uniquement les statistiques
            show_current_data_stats(db)
            
        elif args.action == "populate":
            # Peupler les données
            if args.force:
                stats = populate_test_data(db)
                print(f"✅ Données créées: {stats}")
            else:
                populate_data_interactive(db)
                
        elif args.action == "clear":
            # Vider les données
            if args.force:
                clear_all_data(db)
                print("✅ Données supprimées")
            else:
                clear_data_interactive(db)
                
        elif args.action == "reset":
            # Réinitialiser (vider + peupler)
            if args.force:
                clear_all_data(db)
                stats = populate_test_data(db)
                print(f"✅ Base réinitialisée: {stats}")
            else:
                reset_and_populate(db)
    
    except KeyboardInterrupt:
        print("\n❌ Opération interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main() 