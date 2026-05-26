"""Renomme les labels de tous les groups pour utiliser le nom hébreu de la matière.

Avant : "TEFILA ז-1"
Après : "ביאורי תפילה ז-1"
"""

from __future__ import annotations
import os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")

from sqlalchemy.orm import sessionmaker
from app.db.base import engine
import app.models  # noqa: F401
from app.models import Group, Subject, Class


def main():
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = Session()

    groups = db.query(Group).all()
    print(f"Found {len(groups)} groups")
    renamed = 0
    for g in groups:
        subj = db.get(Subject, g.subject_id)
        if not subj:
            continue
        # source_classes peut être vide; on prend la première classe ou on garde Group générique
        classes = list(g.source_classes)
        suffix = classes[0].code if classes else f"G{g.grade_id}"
        new_label = f"{subj.name_he} {suffix}"
        if g.label != new_label:
            g.label = new_label
            renamed += 1
    db.commit()
    print(f"✓ {renamed} groups relabellisés en hébreu")


if __name__ == "__main__":
    main()
