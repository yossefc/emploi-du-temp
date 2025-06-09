#!/usr/bin/env python3
"""
Script simple pour créer un utilisateur de test dans SQLite
"""
import sqlite3
import hashlib
import os

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_test_user():
    """Create a test user in the database."""
    # Connect to SQLite database
    db_path = "school_timetable.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@example.com",))
        if cursor.fetchone():
            print("✅ L'utilisateur admin@example.com existe déjà.")
        else:
            # Create test user
            hashed_password = hash_password("password123")
            cursor.execute("""
                INSERT INTO users (email, username, hashed_password, role, is_active, language_preference)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("admin@example.com", "admin", hashed_password, "admin", True, "fr"))
            
            conn.commit()
            print("✅ Utilisateur de test créé avec succès!")
            print("   Email: admin@example.com")
            print("   Mot de passe: password123")
            print("   Rôle: admin")
        
        # Check total users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"📊 Total d'utilisateurs dans la base: {user_count}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_test_user() 