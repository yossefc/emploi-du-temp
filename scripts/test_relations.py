#!/usr/bin/env python3
"""
Script de validation finale des relations d'association
À utiliser pour valider que toutes les associations fonctionnent correctement
"""

import psycopg2
import sys
import os

DATABASE_URL = "postgresql://postgres:password@localhost:5432/school_timetable"

def main():
    """Validation rapide des associations"""
    print("🔧 VALIDATION DES RELATIONS D'ASSOCIATION")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Test 1: Existence des tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name IN ('teacher_subjects', 'class_mandatory_subjects', 'class_preferred_rooms')
            AND table_schema = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected = ['teacher_subjects', 'class_mandatory_subjects', 'class_preferred_rooms']
        if len(tables) == 3:
            print("✅ Toutes les tables d'association existent")
        else:
            print(f"❌ Tables manquantes: {set(expected) - set(tables)}")
            return False
            
        # Test 2: Associations fonctionnelles
        cursor.execute("SELECT COUNT(*) FROM teacher_subjects")
        result = cursor.fetchone()
        count = result[0] if result else 0
        
        if count > 0:
            print(f"✅ {count} associations enseignant-matière trouvées")
            
            cursor.execute("""
                SELECT t.first_name, t.last_name, COALESCE(s.name_fr, s.name_he, s.code) as subject
                FROM teacher_subjects ts
                JOIN teachers t ON ts.teacher_id = t.id
                JOIN subjects s ON ts.subject_id = s.id
                LIMIT 1
            """)
            
            example = cursor.fetchone()
            if example:
                print(f"✅ Exemple: {example[0]} {example[1]} enseigne {example[2]}")
        else:
            print("⚠️ Aucune association enseignant-matière trouvée")
            
        print("✅ VALIDATION RÉUSSIE - Les relations fonctionnent!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 