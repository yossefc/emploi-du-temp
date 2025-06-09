"""Add bilingual support to subjects

Revision ID: 52720f5c6cbb
Revises: 55d2c0585030
Create Date: 2025-06-09 12:21:46.850738

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '52720f5c6cbb'
down_revision = '55d2c0585030'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create new enum type
    subject_type_enum = sa.Enum('OBLIGATOIRE', 'OPTIONNELLE', 'SPECIALISEE', 'ACADEMIC', 'SPORTS', 'ARTS', 'RELIGIOUS', 'LANGUAGE', 'SCIENCE_LAB', name='subjecttype')
    
    # For SQLite, we need to recreate the table with new structure
    connection = op.get_bind()
    
    # Create a new table with the updated structure
    op.create_table('subjects_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('nom_fr', sa.String(length=255), nullable=False),
        sa.Column('nom_he', sa.String(length=255), nullable=False),
        sa.Column('name_fr', sa.String(length=255), nullable=True),
        sa.Column('name_he', sa.String(length=255), nullable=True),
        sa.Column('niveau_requis', sa.String(length=50), nullable=False),
        sa.Column('heures_semaine', sa.Integer(), nullable=False),
        sa.Column('type_matiere', subject_type_enum, nullable=False),
        sa.Column('description_fr', sa.Text(), nullable=True),
        sa.Column('description_he', sa.Text(), nullable=True),
        sa.Column('subject_type', subject_type_enum, nullable=True),
        sa.Column('requires_lab', sa.Boolean(), nullable=True),
        sa.Column('requires_special_room', sa.Boolean(), nullable=True),
        sa.Column('requires_consecutive_hours', sa.Boolean(), nullable=True),
        sa.Column('max_hours_per_day', sa.Integer(), nullable=True),
        sa.Column('is_religious', sa.Boolean(), nullable=True),
        sa.Column('requires_gender_separation', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_subjects_new_code', 'subjects_new', ['code'], unique=True)
    op.create_index('ix_subjects_new_id', 'subjects_new', ['id'], unique=False)
    
    # Migrate data from old table to new table
    connection.execute(
        sa.text("""
            INSERT INTO subjects_new (
                id, code, nom_fr, nom_he, name_fr, name_he, 
                niveau_requis, heures_semaine, type_matiere,
                subject_type, requires_lab, requires_special_room,
                requires_consecutive_hours, max_hours_per_day,
                is_religious, requires_gender_separation
            )
            SELECT 
                id, code, 
                COALESCE(name_fr, 'Matière') as nom_fr,
                COALESCE(name_he, 'מקצוע') as nom_he,
                name_fr, name_he,
                '6ème' as niveau_requis,
                2 as heures_semaine,
                'OBLIGATOIRE' as type_matiere,
                COALESCE(subject_type, 'ACADEMIC') as subject_type,
                COALESCE(requires_lab, 0) as requires_lab,
                COALESCE(requires_special_room, 0) as requires_special_room,
                COALESCE(requires_consecutive_hours, 0) as requires_consecutive_hours,
                COALESCE(max_hours_per_day, 2) as max_hours_per_day,
                COALESCE(is_religious, 0) as is_religious,
                COALESCE(requires_gender_separation, 0) as requires_gender_separation
            FROM subjects
        """)
    )
    
    # Drop the old table
    op.drop_table('subjects')
    
    # Rename the new table
    op.rename_table('subjects_new', 'subjects')


def downgrade() -> None:
    # For downgrade, recreate the original table structure
    connection = op.get_bind()
    subject_type_enum = sa.Enum('ACADEMIC', 'SPORTS', 'ARTS', 'RELIGIOUS', 'LANGUAGE', 'SCIENCE_LAB', name='subjecttype')
    
    # Create original table structure
    op.create_table('subjects_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name_he', sa.String(), nullable=False),
        sa.Column('name_fr', sa.String(), nullable=False),
        sa.Column('subject_type', subject_type_enum, nullable=True),
        sa.Column('requires_lab', sa.Boolean(), nullable=True),
        sa.Column('requires_special_room', sa.Boolean(), nullable=True),
        sa.Column('requires_consecutive_hours', sa.Boolean(), nullable=True),
        sa.Column('max_hours_per_day', sa.Integer(), nullable=True),
        sa.Column('is_religious', sa.Boolean(), nullable=True),
        sa.Column('requires_gender_separation', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Migrate data back
    connection.execute(
        sa.text("""
            INSERT INTO subjects_old (
                id, code, name_fr, name_he, subject_type,
                requires_lab, requires_special_room, requires_consecutive_hours,
                max_hours_per_day, is_religious, requires_gender_separation
            )
            SELECT 
                id, code, nom_fr, nom_he, subject_type,
                requires_lab, requires_special_room, requires_consecutive_hours,
                max_hours_per_day, is_religious, requires_gender_separation
            FROM subjects
        """)
    )
    
    # Drop new table and rename old
    op.drop_table('subjects')
    op.rename_table('subjects_old', 'subjects')
    
    # Recreate indexes
    op.create_index('ix_subjects_code', 'subjects', ['code'], unique=True)
    op.create_index('ix_subjects_id', 'subjects', ['id'], unique=False) 