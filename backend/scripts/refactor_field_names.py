#!/usr/bin/env python3
"""
Script pour refactorer automatiquement les anciens noms de champs
vers les nouveaux noms en anglais dans tout le codebase.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


# Mapping des anciens noms vers les nouveaux
FIELD_MAPPINGS = {
    # ClassGroup
    'nom': 'name',
    'niveau': 'grade_name',
    'effectif': 'student_count',
    'horaires_preferes': 'preferred_schedules',
    
    # Room
    'capacite': 'capacity',
}

# Patterns à rechercher et remplacer
PATTERNS = [
    # Accès direct aux attributs
    (r'\.nom\b', '.name'),
    (r'\.niveau\b', '.grade_name'),
    (r'\.effectif\b', '.student_count'),
    (r'\.horaires_preferes\b', '.preferred_schedules'),
    (r'\.capacite\b', '.capacity'),
    
    # Dans les dictionnaires et JSON
    (r'"nom":', '"name":'),
    (r'"niveau":', '"grade_name":'),
    (r'"effectif":', '"student_count":'),
    (r'"horaires_preferes":', '"preferred_schedules":'),
    (r'"capacite":', '"capacity":'),
    
    # Dans les requêtes SQL
    (r'\bnom\s*=', 'name ='),
    (r'\bniveau\s*=', 'grade_name ='),
    (r'\beffectif\s*=', 'student_count ='),
    (r'\bhoraires_preferes\s*=', 'preferred_schedules ='),
    (r'\bcapacite\s*=', 'capacity ='),
    
    # Dans les schemas Pydantic
    (r'nom:\s*str', 'name: str'),
    (r'niveau:\s*str', 'grade_name: str'),
    (r'effectif:\s*int', 'student_count: int'),
    (r'horaires_preferes:\s*', 'preferred_schedules: '),
    (r'capacite:\s*int', 'capacity: int'),
]

# Extensions de fichiers à traiter
FILE_EXTENSIONS = ['.py', '.tsx', '.ts', '.jsx', '.js']

# Dossiers à exclure
EXCLUDE_DIRS = ['node_modules', '.git', '__pycache__', 'venv', 'env', '.env', 'migrations']


def should_process_file(file_path: Path) -> bool:
    """Détermine si un fichier doit être traité."""
    # Vérifier l'extension
    if file_path.suffix not in FILE_EXTENSIONS:
        return False
    
    # Vérifier les dossiers exclus
    for exclude in EXCLUDE_DIRS:
        if exclude in file_path.parts:
            return False
    
    # Ne pas traiter ce script lui-même
    if file_path.name == 'refactor_field_names.py':
        return False
    
    return True


def refactor_file(file_path: Path, dry_run: bool = True) -> List[Tuple[int, str, str]]:
    """
    Refactore un fichier en remplaçant les anciens noms.
    
    Returns:
        Liste des modifications (ligne, ancien, nouveau)
    """
    changes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
        
        modified_content = content
        modified_lines = lines.copy()
        
        # Appliquer chaque pattern
        for old_pattern, new_pattern in PATTERNS:
            for i, line in enumerate(lines):
                if re.search(old_pattern, line):
                    new_line = re.sub(old_pattern, new_pattern, line)
                    if new_line != line:
                        changes.append((i + 1, line.strip(), new_line.strip()))
                        modified_lines[i] = new_line
            
            # Aussi remplacer dans le contenu global
            modified_content = re.sub(old_pattern, new_pattern, modified_content)
        
        # Écrire les modifications si pas en dry run
        if not dry_run and changes:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"✅ Modified {file_path}")
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
    
    return changes


def find_files_to_process(root_dir: Path) -> List[Path]:
    """Trouve tous les fichiers à traiter."""
    files = []
    
    for file_path in root_dir.rglob('*'):
        if file_path.is_file() and should_process_file(file_path):
            files.append(file_path)
    
    return files


def generate_report(all_changes: Dict[Path, List[Tuple[int, str, str]]]) -> None:
    """Génère un rapport des modifications."""
    print("\n" + "=" * 80)
    print("RAPPORT DE REFACTORING")
    print("=" * 80)
    
    total_files = len(all_changes)
    total_changes = sum(len(changes) for changes in all_changes.values())
    
    print(f"\nTotal fichiers modifiés: {total_files}")
    print(f"Total modifications: {total_changes}")
    
    if total_changes > 0:
        print("\nDétail par fichier:")
        print("-" * 80)
        
        for file_path, changes in sorted(all_changes.items()):
            if changes:
                print(f"\n📄 {file_path} ({len(changes)} modifications)")
                for line_num, old, new in changes[:5]:  # Afficher max 5 exemples
                    print(f"  Ligne {line_num}:")
                    print(f"    - {old}")
                    print(f"    + {new}")
                if len(changes) > 5:
                    print(f"  ... et {len(changes) - 5} autres modifications")


def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Refactorer les noms de champs français vers l'anglais")
    parser.add_argument('--root', type=str, default='backend', help='Dossier racine à traiter')
    parser.add_argument('--dry-run', action='store_true', help='Mode simulation (pas de modification)')
    parser.add_argument('--frontend', action='store_true', help='Inclure aussi le dossier frontend')
    
    args = parser.parse_args()
    
    # Déterminer les dossiers à traiter
    dirs_to_process = [Path(args.root)]
    if args.frontend:
        dirs_to_process.append(Path('frontend'))
    
    print(f"🔍 Recherche des fichiers à traiter dans: {', '.join(str(d) for d in dirs_to_process)}")
    print(f"Mode: {'SIMULATION' if args.dry_run else 'MODIFICATION RÉELLE'}")
    
    all_changes = {}
    
    for root_dir in dirs_to_process:
        if not root_dir.exists():
            print(f"⚠️  Le dossier {root_dir} n'existe pas")
            continue
        
        files = find_files_to_process(root_dir)
        print(f"\nTrouvé {len(files)} fichiers à analyser dans {root_dir}")
        
        for file_path in files:
            changes = refactor_file(file_path, dry_run=args.dry_run)
            if changes:
                all_changes[file_path] = changes
    
    # Générer le rapport
    generate_report(all_changes)
    
    if args.dry_run and all_changes:
        print("\n⚠️  Mode simulation - aucun fichier n'a été modifié")
        print("Relancez sans --dry-run pour appliquer les modifications")


if __name__ == "__main__":
    main()