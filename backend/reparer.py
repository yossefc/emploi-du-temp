# -*- coding: utf-8 -*-
r"""Reparation ciblee — 13/08 (bug trous מגמה + י-2 חנ"מ).

    python reparer.py

Corrige en une passe, en figeant tout le reste du planning :
  · י-2 (חנ"מ) : 5 jours, fin <= P7  (32h / 5 jours = 6,4h — P6 impossible)
  · יב-1 / יב-2 / יב-3 : trous elimines (bug des filieres de מגמה corrige)
Seules ces 4 classes sont retravaillees -> quelques minutes.
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
print(f"  י-2 : {n} contraintes ajoutees (fin <= P7)")

last = db.query(Schedule).order_by(Schedule.id.desc()).first()
print(f"  point de depart : schedule {last.id} — {last.name}")
os.environ["FREEZE_EXCEPT"] = "י-2,יב-1,יב-2,יב-3"
os.environ["W_BOOST"] = "1"
os.environ["SOLVER_STAGNATION"] = "420"
os.environ["STRICT_RELAX"] = "spread1,tgap3,lyc2"

eng = TimetableEngine(db, school_id=S)
ctx, solver, status, _ = eng._build_and_solve(set(), 1500, use_assumptions=False, strict=True)
print("  ->", solver.StatusName(status))
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    eng.save_warm_start(ctx, solver)
    res = eng._save_solution(ctx, solver, 'תשפ"ז repare', [], solver.WallTime(), strict=True)
    print("\n  *** REPARE ***", res)
else:
    print("\n  Trop contraint en figeant le reste — previens Claude.")
print("  Envoie cette ligne a Claude.")
