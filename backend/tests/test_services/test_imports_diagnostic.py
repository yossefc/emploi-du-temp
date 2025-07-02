"""Diagnostic des imports pour identifier le probleme."""
import os
import sys

def test_python_path():
    """Verifier le chemin Python."""
    assert "backend" in os.getcwd() or "emploi" in os.getcwd()

def test_app_module_exists():
    """Verifier que le module app existe."""
    import os
    app_path = os.path.join(os.getcwd(), "app")
    assert os.path.exists(app_path), f"Dossier app non trouve dans {os.getcwd()}"
    
    init_path = os.path.join(app_path, "__init__.py")
    services_path = os.path.join(app_path, "services")
    
    print(f"app/ existe: {os.path.exists(app_path)}")
    print(f"app/__init__.py existe: {os.path.exists(init_path)}")
    print(f"app/services/ existe: {os.path.exists(services_path)}")

def test_services_structure():
    """Verifier la structure du dossier services."""
    import os
    
    services_path = os.path.join(os.getcwd(), "app", "services")
    if os.path.exists(services_path):
        files = os.listdir(services_path)
        print(f"Fichiers dans app/services/: {files}")
        
        expected_files = ["__init__.py", "base.py", "teacher_service.py"]
        for expected in expected_files:
            exists = expected in files
            print(f"{expected}: {'✅' if exists else '❌'}")
            
        return len(files) > 0
    else:
        print("❌ Dossier app/services/ n'existe pas")
        return False

def test_try_import_core():
    """Essayer d'importer le module core."""
    try:
        from app.core.exceptions import ValidationException
        print("✅ app.core.exceptions import réussi")
        return True
    except ImportError as e:
        print(f"❌ Import app.core.exceptions échoué: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Autre erreur app.core.exceptions: {e}")
        return False

def test_try_import_base_service():
    """Essayer d'importer BaseService avec gestion d'erreur."""
    try:
        from app.services.base import BaseService
        print("✅ app.services.base import réussi")
        return True
    except ImportError as e:
        print(f"❌ Import app.services.base échoué: {e}")
        return False
    except SyntaxError as e:
        print(f"🚨 ERREUR SYNTAXE dans app.services.base: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Autre erreur app.services.base: {e}")
        return False

def test_try_import_teacher_service():
    """Essayer d'importer TeacherService avec gestion d'erreur."""
    try:
        from app.services.teacher_service import TeacherService
        print("✅ app.services.teacher_service import réussi")
        return True
    except ImportError as e:
        print(f"❌ Import app.services.teacher_service échoué: {e}")
        return False
    except SyntaxError as e:
        print(f"🚨 ERREUR SYNTAXE dans app.services.teacher_service: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Autre erreur app.services.teacher_service: {e}")
        return False

def test_check_file_encoding():
    """Verifier l'encodage des fichiers services."""
    import os
    
    files_to_check = [
        "app/services/__init__.py",
        "app/services/base.py", 
        "app/services/teacher_service.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                null_bytes = content.count(b'\x00')
                has_bom = content.startswith(b'\xef\xbb\xbf')
                
                print(f"{file_path}:")
                print(f"  Taille: {len(content)} bytes")
                print(f"  Null bytes: {null_bytes}")
                print(f"  BOM: {'⚠️' if has_bom else '✅'}")
                
                if null_bytes > 0:
                    print(f"  🚨 PROBLEME: {null_bytes} null bytes détectés!")
                    
            except Exception as e:
                print(f"❌ Erreur lecture {file_path}: {e}")
        else:
            print(f"❌ {file_path} n'existe pas")

class TestImportDiagnostic:
    """Classe de test pour diagnostic des imports."""
    
    def test_basic_imports(self):
        """Test imports Python de base."""
        from typing import Dict, List, Optional
        from unittest.mock import Mock
        assert all([Dict, List, Optional, Mock])
    
    def test_path_diagnostic(self):
        """Test diagnostic du chemin."""
        import sys
        import os
        
        current_dir = os.getcwd()
        print(f"Répertoire actuel: {current_dir}")
        print(f"Python path: {sys.path[:3]}...")  # Premiers éléments
        
        # Vérifier que le répertoire courant est dans le path
        assert current_dir in sys.path or any(current_dir in p for p in sys.path)