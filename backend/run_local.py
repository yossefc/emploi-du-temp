# -*- coding: utf-8 -*-
r"""Generation תשפ"ז — ESCALIER v6 (14/08).

    python corriger_donnees.py     <-- une seule fois
    python run_local.py

Marches par difficulte croissante. Une marche qui echoue est SAUTEE.
Les regles lourdes (depart commun des מגמות, blocs lycee) sont a la fin :
on securise d'abord un planning propre, on tente le reste ensuite.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")
os.environ.setdefault("PAIRS_SKIP", "ז-2,י-2")
os.environ.setdefault("MID3_SKIP", "מתמטיקה")
os.environ["MEGA_SYNC"] = "0"

try:
    from sqlalchemy.orm import sessionmaker
    from ortools.sat.python import cp_model
except ModuleNotFoundError as exc:
    print(f"\n  Module manquant : {exc.name}")
    print(f'\n      "{sys.executable}" -m pip install sqlalchemy ortools\n')
    sys.exit(1)

from app.db.base import engine
import app.models
from app.solver.engine import TimetableEngine

db = sessionmaker(bind=engine)()
eng = TimetableEngine(db, school_id=2)
OK = (cp_model.OPTIMAL, cp_model.FEASIBLE)

ALL = ["gaps", "start", "end", "allday", "split", "pairs", "meg2", "samet",
       "ment3", "math5", "run4", "mid3", "megastart", "meet", "end6", "lyc2",
       "meg4",
       "spread1", "tgap3"]
def relax(*durcies):
    return ",".join(r for r in ALL if r not in durcies)

D1 = ("gaps", "start", "end", "allday")
D2 = D1 + ("split",)
D3 = D2 + ("pairs", "meg2")
D4 = D3 + ("samet", "ment3", "math5")
D5 = D4 + ("run4", "mid3", "megastart", "meet")
D6 = D5 + ("lyc2",)
D7 = D6 + ("meg4",)
D8 = tuple(ALL)

D6b = D5 + ("end6",)
D7b = D6b + ("lyc2",)
D8b = D7b + ("meg4",)

LADDER = [
    ("1 — ELEVES : 0 trou, depart P1, 5 jours", D1, 1500, "0"),
    ("2 — + DEPART COMMUN des מגמות (בגו jusqu'a P11, les autres s'arretent)", D1, 1500, "1"),
    ("3 — + matiere jamais coupee dans la journee", D2, 1500, "1"),
    ("4 — + blocs de 2h en חטיבה", D3, 1800, "1"),
    ("5 — + max 4h/jour meme prof-classe, מנטורים 2h, blocs de maths des P5,"
     " suite de 4h a partir de P6", D4 + ("run4",), 1800, "1"),
    ("6 — + jamais 3h en milieu de journee, fenetres מגמות/reunions", D5, 1800, "1"),
    ("7 — + aucune journee ne finit avant P6 (sauf lundi)", D6b, 1800, "1"),
    ("8 — + jamais 4h d'affilee au lycee, היסטוריה/אזרחות 2h/jour", D7b, 1800, "1"),
    ("9 — + מגמות max 3h hors fin de journee", D8b, 1500, "1"),
    ("10 — + aucune attente de 3h chez les profs", tuple(ALL), 1800, "1"),
]

print("\n=== PREPARATION (s'arrete seule quand elle stagne) ===", flush=True)
os.environ["W_BOOST"] = "25"; os.environ["SOLVER_STAGNATION"] = "600"
os.environ["STRICT_RELAX"] = ""
ctx, solver, status, _ = eng._build_and_solve(set(), 2400, use_assumptions=False, strict=False)
print("  ->", solver.StatusName(status), flush=True)
if status not in OK:
    sys.exit("  echec preparation — previens Claude")
eng.save_warm_start(ctx, solver)
best = eng._save_solution(ctx, solver, 'תשפ"ז base', [], solver.WallTime())
print("  base :", best, flush=True)

os.environ["W_BOOST"] = "1"
derniere = None
for titre, durcies, budget, megasync in LADDER:
    print(f"\n=== Marche {titre} ===", flush=True)
    os.environ["STRICT_RELAX"] = relax(*durcies)
    os.environ["MEGA_SYNC"] = megasync
    os.environ["SOLVER_STAGNATION"] = "480"
    ctx, solver, status, _ = eng._build_and_solve(set(), budget, use_assumptions=False, strict=True)
    nom = solver.StatusName(status)
    print("  ->", nom, flush=True)
    if status in OK:
        eng.save_warm_start(ctx, solver)
        best = eng._save_solution(ctx, solver, f'תשפ"ז marche {titre[:1]}', [],
                                  solver.WallTime(), strict=True)
        derniere = titre
        print("  reussi :", best, flush=True)
    else:
        print(f"  sautee ({nom}) — on garde la precedente", flush=True)

print("\n=== TERMINE ===")
print("Derniere marche reussie :", derniere)
print("Meilleur planning :", best)
print("Envoie ces deux lignes a Claude.", flush=True)
