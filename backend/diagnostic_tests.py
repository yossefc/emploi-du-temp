#!/usr/bin/env python3
"""
Script de diagnostic pour identifier et resoudre les problemes de tests.
"""
import os
import sys
from pathlib import Path

def check_file_encoding(file_path):
    """Verifie l'encodage et detecte les null bytes dans un fichier."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Detecter les null bytes
        null_bytes = content.count(b'\x00')
        
        # Essayer de decoder en UTF-8
        try:
            text_content = content.decode('utf-8')
            encoding_ok = True
        except UnicodeDecodeError:
            encoding_ok = False
            text_content = None
        
        return {
            'file': file_path,
            'size': len(content),
            'null_bytes': null_bytes,
            'encoding_ok': encoding_ok,
            'has_bom': content.startswith(b'\xef\xbb\xbf'),
            'first_100_bytes': content[:100]
        }
    except Exception as e:
        return {
            'file': file_path,
            'error': str(e)
        }

def clean_file(file_path):
    """Nettoie un fichier en supprimant les null bytes et normalisant l'encodage."""
    try:
        # Lire le contenu
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Supprimer les null bytes
        clean_content = content.replace(b'\x00', b'')
        
        # Supprimer le BOM si present
        if clean_content.startswith(b'\xef\xbb\xbf'):
            clean_content = clean_content[3:]
        
        # Decoder et re-encoder proprement
        try:
            text = clean_content.decode('utf-8')
            # Normaliser les fins de ligne
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            
            # Reecrire le fichier
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
            
            return True, f"Fichier nettoye: {file_path}"
        except Exception as e:
            return False, f"Erreur de decodage: {e}"
            
    except Exception as e:
        return False, f"Erreur: {e}"

def main():
    """Fonction principale de diagnostic."""
    print("=== DIAGNOSTIC DES FICHIERS DE TEST ===\n")
    
    # Dossier des tests
    test_dir = Path("tests/test_services")
    
    if not test_dir.exists():
        print(f"❌ Dossier {test_dir} non trouve!")
        return
    
    print(f"📁 Analyse du dossier: {test_dir}\n")
    
    # Analyser tous les fichiers Python
    python_files = list(test_dir.glob("*.py"))
    
    if not python_files:
        print("❌ Aucun fichier Python trouve!")
        return
    
    print(f"📄 Fichiers trouves: {len(python_files)}\n")
    
    problematic_files = []
    
    for file_path in python_files:
        print(f"🔍 Analyse: {file_path.name}")
        
        result = check_file_encoding(file_path)
        
        if 'error' in result:
            print(f"  ❌ Erreur: {result['error']}")
            continue
        
        print(f"  📊 Taille: {result['size']} bytes")
        print(f"  🔍 Null bytes: {result['null_bytes']}")
        print(f"  📝 Encodage UTF-8: {'✅' if result['encoding_ok'] else '❌'}")
        print(f"  🏷️  BOM present: {'⚠️' if result['has_bom'] else '✅'}")
        
        if result['null_bytes'] > 0 or not result['encoding_ok'] or result['has_bom']:
            problematic_files.append(file_path)
            print(f"  ⚠️  PROBLEME DETECTE!")
            
            # Afficher les premiers bytes pour diagnostic
            print(f"  🔢 Premiers bytes: {result['first_100_bytes']}")
        
        print()
    
    # Proposer de nettoyer les fichiers problematiques
    if problematic_files:
        print(f"🚨 {len(problematic_files)} fichier(s) problematique(s) detecte(s):")
        for f in problematic_files:
            print(f"  - {f.name}")
        
        print("\n🔧 NETTOYAGE AUTOMATIQUE:")
        for file_path in problematic_files:
            success, message = clean_file(file_path)
            if success:
                print(f"  ✅ {message}")
            else:
                print(f"  ❌ {message}")
    
    else:
        print("✅ Tous les fichiers semblent corrects!")
    
    print("\n=== VERIFICATION POST-NETTOYAGE ===")
    
    # Re-verifier tous les fichiers
    all_clean = True
    for file_path in python_files:
        result = check_file_encoding(file_path)
        if 'error' not in result and (result['null_bytes'] > 0 or not result['encoding_ok']):
            print(f"❌ {file_path.name} a encore des problemes")
            all_clean = False
    
    if all_clean:
        print("✅ Tous les fichiers sont maintenant propres!")
        print("\n🚀 Vous pouvez maintenant lancer:")
        print("   python -m pytest tests/test_services -v")
    else:
        print("❌ Certains fichiers ont encore des problemes")
    
    print("\n=== TESTS DE SYNTAXE ===")
    
    # Tester la syntaxe Python de chaque fichier
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Compiler pour verifier la syntaxe
            compile(content, str(file_path), 'exec')
            print(f"✅ {file_path.name}: Syntaxe correcte")
            
        except SyntaxError as e:
            print(f"❌ {file_path.name}: Erreur de syntaxe ligne {e.lineno}: {e.msg}")
            all_clean = False
        except Exception as e:
            print(f"⚠️  {file_path.name}: Erreur: {e}")
    
    if all_clean:
        print("\n🎉 DIAGNOSTIC COMPLET: Tous les fichiers sont prets!")
    else:
        print("\n⚠️  DIAGNOSTIC: Des problemes subsistent")

if __name__ == "__main__":
    main()