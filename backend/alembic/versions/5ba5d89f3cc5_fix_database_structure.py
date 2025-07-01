"""fix_database_structure

Revision ID: 5ba5d89f3cc5
Revises: ae752a6c2082
Create Date: 2025-07-01 18:18:51.693519

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = '5ba5d89f3cc5'
down_revision = 'ae752a6c2082'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply database structure fixes and normalizations."""
    
    # 1. Create class_subject_requirements table
    op.create_table(
        'class_subject_requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('hours_per_week', sa.Integer(), nullable=False),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.ForeignKeyConstraint(['class_id'], ['class_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('class_id', 'subject_id', name='uq_class_subject')
    )
    
    # 2. Migrate data from class_group_subjects to class_subject_requirements
    # First, copy existing associations with default values
    op.execute("""
        INSERT INTO class_subject_requirements (class_id, subject_id, hours_per_week, is_mandatory)
        SELECT cgs.class_group_id, cgs.subject_id, 2, 1
        FROM class_group_subjects cgs
        WHERE NOT EXISTS (
            SELECT 1 FROM class_subject_requirements csr 
            WHERE csr.class_id = cgs.class_group_id AND csr.subject_id = cgs.subject_id
        )
    """)
    
    # 3. Add new columns to teachers table
    op.add_column('teachers', sa.Column('hire_date', sa.Date(), nullable=True))
    op.add_column('teachers', sa.Column('contract_type', sa.String(50), nullable=True))
    op.add_column('teachers', sa.Column('notes', sa.Text(), nullable=True))
    
    # 4. Add new columns to subjects table
    op.add_column('subjects', sa.Column('color_hex', sa.String(7), nullable=True))
    op.add_column('subjects', sa.Column('abbreviation', sa.String(10), nullable=True))
    op.add_column('subjects', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')))
    
    # 5. Add created_at and updated_at to class_groups table
    op.add_column('class_groups', sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()))
    op.add_column('class_groups', sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now()))
    
    # 6. Normalize class_groups table - remove duplicate columns
    # Drop the old columns that are duplicates of the French ones
    op.drop_column('class_groups', 'name')
    op.drop_column('class_groups', 'grade') 
    op.drop_column('class_groups', 'student_count')
    
    # 7. Make the French columns non-nullable and properly named
    op.alter_column('class_groups', 'nom', new_column_name='name', nullable=False)
    op.alter_column('class_groups', 'niveau', new_column_name='grade_level', nullable=False)
    op.alter_column('class_groups', 'effectif', new_column_name='student_count', nullable=False)
    
    # 8. Create performance indexes
    # Index for schedule entries lookup
    op.create_index(
        'idx_schedule_entries_lookup',
        'schedule_entries',
        ['schedule_id', 'day_of_week', 'period']
    )
    
    # Index for teacher availability (assuming this table exists or will be created)
    # Note: This assumes teacher_availabilities table exists
    try:
        op.create_index(
            'idx_teacher_availability',
            'teacher_availabilities',
            ['teacher_id', 'day_of_week']
        )
    except Exception:
        # If teacher_availabilities table doesn't exist, skip this index
        pass
    
    # 9. Add index on class_subject_requirements for faster lookups
    op.create_index(
        'idx_class_subject_requirements_class',
        'class_subject_requirements',
        ['class_id']
    )
    
    op.create_index(
        'idx_class_subject_requirements_subject',
        'class_subject_requirements',
        ['subject_id']
    )


def downgrade() -> None:
    """Revert database structure changes."""
    
    # Remove indexes
    op.drop_index('idx_class_subject_requirements_subject', table_name='class_subject_requirements')
    op.drop_index('idx_class_subject_requirements_class', table_name='class_subject_requirements')
    
    try:
        op.drop_index('idx_teacher_availability', table_name='teacher_availabilities')
    except Exception:
        pass
        
    op.drop_index('idx_schedule_entries_lookup', table_name='schedule_entries')
    
    # Restore class_groups structure
    op.alter_column('class_groups', 'name', new_column_name='nom', nullable=False)
    op.alter_column('class_groups', 'grade_level', new_column_name='niveau', nullable=False)
    op.alter_column('class_groups', 'student_count', new_column_name='effectif', nullable=False)
    
    # Add back the old duplicate columns
    op.add_column('class_groups', sa.Column('name', sa.String(255), nullable=True))
    op.add_column('class_groups', sa.Column('grade', sa.String(50), nullable=True))
    op.add_column('class_groups', sa.Column('student_count', sa.Integer(), nullable=True))
    
    # Remove timestamps from class_groups
    op.drop_column('class_groups', 'updated_at')
    op.drop_column('class_groups', 'created_at')
    
    # Remove new columns from subjects
    op.drop_column('subjects', 'is_active')
    op.drop_column('subjects', 'abbreviation')
    op.drop_column('subjects', 'color_hex')
    
    # Remove new columns from teachers
    op.drop_column('teachers', 'notes')
    op.drop_column('teachers', 'contract_type')
    op.drop_column('teachers', 'hire_date')
    
    # Migrate data back from class_subject_requirements to class_group_subjects
    op.execute("""
        INSERT OR IGNORE INTO class_group_subjects (class_group_id, subject_id)
        SELECT class_id, subject_id FROM class_subject_requirements
    """)
    
    # Drop the new table
    op.drop_table('class_subject_requirements') 