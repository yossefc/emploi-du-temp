# -*- coding: utf-8 -*-
"""Les reunions du lundi peuvent commencer a P6 (Yossef 14/08)."""
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
    if c.constraint_type != ConstraintType.BLOCK_SLOT_GROUP:
        continue
    if "חלון ישיבה" not in (c.origin_description or ""):
        continue
    p = dict(c.parameters or {})
    if p.get("days") != [1]:
        continue
    slots = [s for s in p.get("slot_indices", []) if s != 5]   # P6 libere
    if slots != p.get("slot_indices"):
        p["slot_indices"] = slots
        c.parameters = p
        n += 1
db.commit()
print(f"  {n} fenetres de reunion elargies : le lundi, P6 est ouvert")
