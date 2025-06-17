#!/usr/bin/env python3
"""
Script simple pour ajouter des données de base.
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = "school_timetable.db"

def add_simple_data():
    """Ajoute des données de base directement avec SQL."""
    
    print("📝 Ajout de données de base avec SQL...")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Vérifier si des données existent déjà
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            print("⚠️  Des données existent déjà, suppression...")
            cursor.execute("DELETE FROM users")
            cursor.execute("DELETE FROM teachers") 
            cursor.execute("DELETE FROM subjects")
            cursor.execute("DELETE FROM class_groups")
            cursor.execute("DELETE FROM rooms")
            conn.commit()
        
        # Créer un utilisateur admin (sans hash de mot de passe pour l'instant)
        cursor.execute("""
            INSERT INTO users (username, email, is_active, hashed_password, role)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", "admin@example.com", True, "admin123", "admin"))
        
        # Créer des matières
        subjects_data = [
            ("MATH", "מתמטיקה", "Mathématiques"),
            ("FR", "צרפתית", "Français"),
            ("HIST", "היסטוריה", "Histoire"),
            ("SCI", "מדעים", "Sciences"),
            ("ENG", "אנגלית", "Anglais"),
            ("HE", "עברית", "Hébreu"),
            ("PE", "חינוך גופני", "Education Physique"),
        ]
        
        cursor.executemany("""
            INSERT INTO subjects (code, name_he, name_fr, subject_type)
            VALUES (?, ?, ?, 'ACADEMIC')
        """, subjects_data)
        
        # Créer des salles
        rooms_data = [
            ("A101", "Salle A101", 30, "classroom"),
            ("A102", "Salle A102", 25, "classroom"),
            ("LAB1", "Laboratoire 1", 20, "laboratory"),
            ("INFO1", "Salle informatique", 20, "computer"),
            ("B201", "Salle B201", 35, "classroom"),
            ("GYM", "Gymnase", 50, "gym"),
        ]
        
        cursor.executemany("""
            INSERT INTO rooms (code, nom, capacite, type_salle, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, rooms_data)
        
        # Créer des classes
        classes_data = [
            ("6E1", "6ème 1", "6", 28, "fr"),
            ("5E2", "5ème 2", "5", 25, "fr"),
            ("4E1", "4ème 1", "4", 30, "fr"),
            ("Y1", "י׳ 1", "10", 22, "he"),
            ("H2", "ח׳ 2", "8", 26, "he"),
        ]
        
        cursor.executemany("""
            INSERT INTO class_groups (code, nom, niveau, effectif, primary_language, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, classes_data)
        
        # Créer des enseignants
        teachers_data = [
            ("T001", "Jean", "Dupont", "jean.dupont@school.com", 25, "fr"),
            ("T002", "Marie", "Martin", "marie.martin@school.com", 20, "fr"),
            ("T003", "Sarah", "Cohen", "sarah.cohen@school.com", 18, "he"),
            ("T004", "David", "Levy", "david.levy@school.com", 22, "he"),
            ("T005", "Emma", "Dubois", "emma.dubois@school.com", 15, "fr"),
        ]
        
        cursor.executemany("""
            INSERT INTO teachers (code, first_name, last_name, email, max_hours_per_week, primary_language, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, teachers_data)
        
        # Associer quelques matières aux enseignants
        # Récupérer les IDs
        cursor.execute("SELECT id FROM subjects WHERE code = 'MATH'")
        math_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM subjects WHERE code = 'FR'")
        fr_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM subjects WHERE code = 'HIST'")
        hist_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM subjects WHERE code = 'SCI'")
        sci_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM subjects WHERE code = 'ENG'")
        eng_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM teachers WHERE code = 'T001'")
        jean_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM teachers WHERE code = 'T002'")
        marie_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM teachers WHERE code = 'T003'")
        sarah_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM teachers WHERE code = 'T004'")
        david_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM teachers WHERE code = 'T005'")
        emma_id = cursor.fetchone()[0]
        
        # Créer les associations
        teacher_subject_associations = [
            (jean_id, math_id),
            (marie_id, fr_id),
            (sarah_id, hist_id),
            (david_id, sci_id),
            (emma_id, eng_id),
        ]
        
        cursor.executemany("""
            INSERT INTO teacher_subjects (teacher_id, subject_id)
            VALUES (?, ?)
        """, teacher_subject_associations)
        
        conn.commit()
        
        print("✅ Données ajoutées avec succès !")
        print("   - 7 matières")
        print("   - 5 classes")
        print("   - 6 salles")
        print("   - 5 enseignants")
        print("   - 1 utilisateur admin (admin/admin123)")
        print("   - Associations enseignants-matières")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Ajout de données simples...")
    print("=" * 50)
    
    if add_simple_data():
        print("\n🎉 Succès !")
        print("\nMaintenant vous pouvez :")
        print("  1. Redémarrer le serveur backend")
        print("  2. Tester l'interface frontend")
        print("  3. Voir les vraies données")
    else:
        print("\n❌ Échec") 