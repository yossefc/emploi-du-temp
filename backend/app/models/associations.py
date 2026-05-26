"""Tables d'association many-to-many."""

from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.base import Base


# Quels enseignants sont qualifiés pour quelles matières (HARD constraint utilisée par solveur)
teacher_qualified_subjects = Table(
    "teacher_qualified_subjects",
    Base.metadata,
    Column("teacher_id", Integer, ForeignKey("teachers.id", ondelete="CASCADE"), primary_key=True),
    Column("subject_id", Integer, ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True),
)

# Quels profs enseignent dans un Group (1 prof = cours classique, N profs = co-enseignement / sous-sections)
group_teachers = Table(
    "group_teachers",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
    Column("teacher_id", Integer, ForeignKey("teachers.id", ondelete="CASCADE"), primary_key=True),
)

# Quelles Classes contribuent des élèves à un Group
# - 1 entrée = cours classe entière
# - N entrées = barrette inter-classes (ex: math שכבה-wide)
group_source_classes = Table(
    "group_source_classes",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
    Column("class_id", Integer, ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
)
