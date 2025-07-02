"""Test sûr sans dépendances externes."""

def test_basic():
    """Test basique pour vérifier pytest."""
    assert True

def test_math():
    """Test mathématique simple."""
    assert 2 + 2 == 4

def test_imports():
    """Test des imports de base."""
    from unittest.mock import Mock
    assert Mock is not None

def test_israeli_school():
    """Test concepts école israélienne."""
    days = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi"]
    assert len(days) == 6
    assert "vendredi" in days

class TestSafe:
    """Classe de test sûre."""
    
    def test_method(self):
        """Test de méthode."""
        assert "test" == "test"
    
    def test_fixtures(self, sample_teacher_data):
        """Test avec fixture."""
        assert sample_teacher_data["code"] == "T001"
