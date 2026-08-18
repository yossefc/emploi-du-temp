# -*- coding: utf-8 -*-
"""Retire la preference « anglais en milieu de journee » (Yossef 14/08)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")
from sqlalchemy.orm import sessionmaker
from app.db.base import engine
import app.models
from app.models import Constraint, ConstraintType
db = sessionmaker(bind=engine)()
n = 0
for c in db.query(Constraint).filter_by(school_id=2).all():
    if (c.constraint_type == ConstraintType.SUBJECT_PREFERRED_SLOT_RANGE
            and "אנגלית" in (c.origin_description or "")):
        db.delete(c); n += 1
db.commit()
print(f"  {n} preference(s) retiree(s) : l'anglais se place librement")
