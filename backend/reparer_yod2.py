# -*- coding: utf-8 -*-
r"""Reparation ciblee de י-2 (חינוך מיוחד) — 13/08.

    python reparer_yod2.py

1. Ajoute dans la base : י-2 finit au plus tard P7 (comme ז-2/ח-2, chinuch
   meyuchad). 32h sur 5 jours = 6,4 h/jour, donc P6 est arithmetiquement
   impossible (30 creneaux pour 32h) — P7 est le minimum atteignable.
2. Fige TOUT le planning existant sauf י-2 et ne fait retravailler que cette
   classe : quelques minutes au lieu d'une heure.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")
os.environ.setdefault("PAIRS_SKIP", "ז-2,י-2")
os.environ.setdefault("MID3_SKIP", "מתמטיקה")

from sqlalchemy.orm import sessionmaker
from ortools.sat.python import cp_model
from app.db.base import engine
import app.models
from app.models import (Group, Schedule, Constraint, ConstraintType,
                        ConstraintPriority, ConstraintOriginRole)
from app.solver.engine import TimetableEngine

db = sessionmaker(bind=engine)()
S = 2

gids = [g.id for g in db.query(Group).filter_by(school_id=S).all()
        if any(c.code == "י-2" for c in g.source_classes)]
deja = {(c.parameters or {}).get("target_id")
        for c in db.query(Constraint).filter_by(school_id=S).all()
        if 'י-2 חנ"מ' in (c.origin_description or "")}
n = 0
for gid in gids:
    if gid in deja:
        continue
    db.add(Constraint(
        school_id=S, constraint_type=ConstraintType.BLOCK_SLOT_GROUP,
        priority=ConstraintPriority.HARD,
        parameters={"days": [0, 1, 2, 3, 4], "slot_indices": [7, 8, 9],
                    "target_id": gid},
        origin_role=ConstraintOriginRole.SCHOOL_ADMIN,
        origin_description='י-2 חנ"מ — מסיימת ב-P7 (יוסף 13/08)', is_active=True))
    n += 1
db.commit()
print(f"  {n} contraintes ajoutees : י-2 ne depasse plus P7")

last = db.query(Schedule).order_by(Schedule.id.desc()).first()
print(f"  point de depart : schedule {last.id} — {last.name}")
os.environ["FREEZE_EXCEPT"] = "י-2"
os.environ["W_BOOST"] = "1"
os.environ["SOLVER_STAGNATION"] = "300"
os.environ["STRICT_RELAX"] = "mid3,megastart,meet,spread1,tgap3,lyc2"

eng = TimetableEngine(db, school_id=S)
ctx, solver, status, _ = eng._build_and_solve(set(), 900, use_assumptions=False, strict=True)
print("  ->", solver.StatusName(status))
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    eng.save_warm_start(ctx, solver)
    res = eng._save_solution(ctx, solver, 'תשפ"ז + י-2 reparee', [],
                             solver.WallTime(), strict=True)
    print("\n  *** REPARE ***", res)
    print("  Envoie cette ligne a Claude.")
else:
    print("\n  Reparation impossible en figeant le reste — previens Claude,")
    print("  il elargira la zone a retravailler.")
