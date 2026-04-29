# backend/tests/test_migrations/test_uniformize_names.py

import pytest
from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config
from app.db.base import Base


class TestUniformizeNamesMigration:
    """Test de la migration d'uniformisation des noms."""
    
    @pytest.fixture
    def alembic_config(self, tmp_path):
        """Configuration Alembic pour les tests."""
        config = Config()
        config.set_main_option("script_location", "alembic")
        config.set_main_option("sqlalchemy.url", "sqlite:///:memory:")
        return config
    
    def test_migration_up(self, db_session, alembic_config):
        """Test de la migration vers le haut (upgrade)."""
        # Appliquer toutes les migrations jusqu'à celle-ci
        command.upgrade(alembic_config, "uniformize_field_names")
        
        # Vérifier que les colonnes ont été renommées
        with db_session.bind.connect() as conn:
            # Vérifier class_groups
            result = conn.execute(text(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='class_groups'"
            )).scalar()
            
            assert "name" in result  # Ancien: nom
            assert "grade_name" in result  # Ancien: niveau
            assert "student_count" in result  # Ancien: effectif
            assert "preferred_schedules" in result  # Ancien: horaires_preferes
            
            # Vérifier rooms
            result = conn.execute(text(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='rooms'"
            )).scalar()
            
            assert "capacity" in result  # Ancien: capacite
            
            # Vérifier les indexes
            indexes = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )).fetchall()
            index_names = [idx[0] for idx in indexes]
            
            assert "idx_teacher_availability_lookup" in index_names
            assert "idx_schedule_entries_lookup" in index_names
            assert "idx_class_subject_req" in index_names
    
    def test_migration_down(self, db_session, alembic_config):
        """Test de la migration vers le bas (downgrade)."""
        # D'abord upgrade
        command.upgrade(alembic_config, "uniformize_field_names")
        
        # Puis downgrade
        command.downgrade(alembic_config, "-1")
        
        # Vérifier que les anciens noms sont revenus
        with db_session.bind.connect() as conn:
            result = conn.execute(text(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='class_groups'"
            )).scalar()
            
            assert "nom" in result
            assert "niveau" in result
            assert "effectif" in result
            assert "horaires_preferes" in result
    
    def test_data_preservation(self, db_session, alembic_config):
        """Test que les données sont préservées pendant la migration."""
        # Insérer des données avant la migration
        with db_session.bind.connect() as conn:
            conn.execute(text("""
                INSERT INTO class_groups (code, nom, niveau, effectif)
                VALUES ('6A', 'Sixième A', '6', 25)
            """))
            conn.commit()
        
        # Appliquer la migration
        command.upgrade(alembic_config, "uniformize_field_names")
        
        # Vérifier que les données sont toujours là
        with db_session.bind.connect() as conn:
            result = conn.execute(text(
                "SELECT code, name, grade_name, student_count FROM class_groups"
            )).fetchone()
            
            assert result[0] == '6A'
            assert result[1] == 'Sixième A'
            assert result[2] == '6'
            assert result[3] == 25


# Test d'intégration avec les modèles
class TestModelsAfterMigration:
    """Test des modèles après la migration."""
    
    def test_class_group_model(self, db_session):
        """Test du modèle ClassGroup avec les nouveaux noms."""
        from app.models.class_group import ClassGroup, ClassType
        
        # Créer une instance
        class_group = ClassGroup(
            code="7B",
            name="Septième B",  # Nouveau nom
            grade_name="7",  # Nouveau nom
            student_count=28,  # Nouveau nom
            class_type=ClassType.REGULAR,
            preferred_schedules={"monday": ["morning"]},  # Nouveau nom
            is_active=True
        )
        
        db_session.add(class_group)
        db_session.commit()
        
        # Vérifier
        saved = db_session.query(ClassGroup).filter_by(code="7B").first()
        assert saved.name == "Septième B"
        assert saved.grade_name == "7"
        assert saved.student_count == 28
        assert saved.preferred_schedules == {"monday": ["morning"]}
    
    def test_room_model(self, db_session):
        """Test du modèle Room avec les nouveaux noms."""
        from app.models.room import Room, RoomType
        
        # Créer une instance
        room = Room(
            code="S101",
            name="Salle 101",
            capacity=30,  # Nouveau nom
            type=RoomType.CLASSROOM,
            building="A",
            floor=1,
            equipment={"projector": True, "whiteboard": True}
        )
        
        db_session.add(room)
        db_session.commit()
        
        # Vérifier
        saved = db_session.query(Room).filter_by(code="S101").first()
        assert saved.capacity == 30
        assert saved.can_accommodate(25) is True
        assert saved.can_accommodate(35) is False