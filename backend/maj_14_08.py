# -*- coding: utf-8 -*-
"""Mises a jour du 14/08 : fichier directeur + reponses de Yossef."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")
from sqlalchemy.orm import sessionmaker
from app.db.base import engine
import app.models
from app.models import Group, GroupType, Teacher, Class
db = sessionmaker(bind=engine)()
S = 2

def T(name):
    for t in db.query(Teacher).filter_by(school_id=S).all():
        if name in f"{t.first_name or ''} {t.last_name or ''}":
            return t

groups = db.query(Group).filter_by(school_id=S).all()
ref = next(g for g in groups if g.label.startswith("מתמטיקה ז-1"))

def creer(code, prof, label):
    if any(g.label == label for g in groups):
        print(f"  = {label} existe deja")
        return
    cls = db.query(Class).filter_by(school_id=S, code=code).first()
    g = Group(school_id=S, grade_id=cls.grade_id, subject_id=ref.subject_id,
              label=label, hours_per_week=2,
              group_type=GroupType.WHOLE_CLASS, can_split=False)
    g.source_classes.append(cls)
    t = T(prof)
    if t:
        g.teachers.append(t)
    db.add(g); db.flush()
    print(f"  + {label} 2h -> {prof}")

# Le directeur a deplace les 2h de מולאורי de ח-4 vers ז-4 (fichier du 13/08
# 08:08). Les 2h de ח-4 restent, sans prof pour l'instant.
creer("ז-4", "מולאורי שירן", "מתמטיקה ז-4 (תגבור)")
creer("ח-4", "לא משובץ 19", "מתמטיקה ח-4 (תגבור)")
db.commit()
print("Mise a jour terminee.")
