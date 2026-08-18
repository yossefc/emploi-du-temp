# -*- coding: utf-8 -*-
r"""Mises a jour du 14/08 soir (message de Yossef) :

1. רחום שני : dispo = dimanche + lundi complets, mardi premieres heures
   (P1-P4). Elle garde 2 barrettes au college (ז et ח) — la ט passe a
   לא משובץ, a reassigner.
2. אברהמי : uniquement dimanche, lundi, jeudi (mardi + mercredi fermes).
3. רחלי טובי : dimanche ferme · lundi des P5 · mardi des P6 · mer + jeu libres.
   Et elle reprend le groupe d'anglais de la barrette ט (a la place de
   דיין ישראל) — fichier du directeur.
4. Maths du LYCEE : mercredi = jour de conge des profs de math (les barrettes
   22/23/24 ne tournent pas le mercredi) ; le dimanche s'ouvre — les souhaits
   du dimanche des profs de math du lycee sont retires.

    python maj_15_08.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")
from sqlalchemy.orm import sessionmaker
from app.db.base import engine
import app.models
from app.models import (Group, Teacher, Constraint, ConstraintType,
                        ConstraintPriority, ConstraintOriginRole)
db = sessionmaker(bind=engine)()
S = 2

def T(name):
    for t in db.query(Teacher).filter_by(school_id=S).all():
        if name in f"{t.first_name or ''} {t.last_name or ''}":
            return t

def bloque(t, jours_slots, desc):
    for c in list(db.query(Constraint).filter_by(school_id=S).all()):
        p = c.parameters or {}
        if (c.constraint_type == ConstraintType.BLOCK_SLOT_TEACHER
                and p.get("target_id") == t.id and desc in (c.origin_description or "")):
            db.delete(c)
    for d, slots in jours_slots:
        db.add(Constraint(
            school_id=S, constraint_type=ConstraintType.BLOCK_SLOT_TEACHER,
            priority=ConstraintPriority.HARD,
            parameters={"days": [d], "slot_indices": slots, "target_id": t.id},
            origin_role=ConstraintOriginRole.TEACHER,
            origin_description=desc, is_active=True))

# --- 1. רחום שני -----------------------------------------------------------
rahum = T('רחום')
bloque(rahum, [(2, list(range(4, 11))),          # mardi : que P1-P4
               (3, list(range(11))),             # mercredi ferme
               (4, list(range(11)))],            # jeudi ferme
       'רחום שני — א+ב מלאים, ג שעות ראשונות (יוסף 14/08)')
print("  רחום שני : dim+lun complets, mar P1-P4")
g575 = db.get(Group, 575)                        # מתמטיקה ט barrette
if g575 and any(t.id == rahum.id for t in g575.teachers):
    g575.teachers.remove(rahum)
    libre = T('לא משובץ 17') or T('לא משובץ')
    g575.teachers.append(libre)
    print(f"  רחום שני retiree de la barrette ט (g575) -> {libre.first_name}")

# --- 2. אברהמי -------------------------------------------------------------
avrahami = T('אברהמי')
bloque(avrahami, [(2, list(range(11))), (3, list(range(11)))],
       'אברהמי — ראשון שני חמישי בלבד (יוסף 14/08)')
print("  אברהמי : dimanche, lundi, jeudi uniquement")

# --- 3. רחלי טובי -----------------------------------------------------------
tovi = T('טובי רחלי')
bloque(tovi, [(0, list(range(11))),              # dimanche ferme
              (1, [0, 1, 2, 3]),                 # lundi des P5
              (2, [0, 1, 2, 3, 4])],             # mardi des P6
      'רחלי טובי — ב מP5, ג מP6, ד+ה פנויים (יוסף 14/08)')
print("  רחלי טובי : dim ferme, lun des P5, mar des P6, mer+jeu libres")
g468 = db.get(Group, 468)                        # אנגלית ט — דיין ישראל
dayan_i = T('דיין ישראל')
if g468 and dayan_i and any(t.id == dayan_i.id for t in g468.teachers):
    g468.teachers.remove(dayan_i)
    g468.teachers.append(tovi)
    print("  אנגלית barrette ט : דיין ישראל -> רחלי טובי (fichier directeur)")

# --- 4. maths du lycee ------------------------------------------------------
MATH_LYC_COHORTS = (22, 23, 24)
gids = [g.id for g in db.query(Group).filter_by(school_id=S).all()
        if g.parallel_cohort_id in MATH_LYC_COHORTS]
deja = {(c.parameters or {}).get("target_id")
        for c in db.query(Constraint).filter_by(school_id=S).all()
        if 'מתמטיקה תיכון — רביעי' in (c.origin_description or "")}
n = 0
for gid in gids:
    if gid in deja:
        continue
    db.add(Constraint(
        school_id=S, constraint_type=ConstraintType.BLOCK_SLOT_GROUP,
        priority=ConstraintPriority.HARD,
        parameters={"days": [3], "slot_indices": list(range(11)), "target_id": gid},
        origin_role=ConstraintOriginRole.SCHOOL_ADMIN,
        origin_description='מתמטיקה תיכון — רביעי חופשי למורים (יוסף 14/08)',
        is_active=True))
    n += 1
print(f"  maths lycee : mercredi ferme pour les 3 barrettes ({n} contraintes)")

# le dimanche s'ouvre : on retire les souhaits/fenetres du dimanche des
# profs de math du lycee (בוקריס, קנימח — leurs blocs souples du dimanche)
math_profs = {t.id for g in db.query(Group).filter_by(school_id=S).all()
              if g.parallel_cohort_id in MATH_LYC_COHORTS for t in g.teachers}
m = 0
for c in list(db.query(Constraint).filter_by(school_id=S).all()):
    p = c.parameters or {}
    if p.get("target_id") in math_profs and c.priority == ConstraintPriority.SOFT \
            and c.constraint_type == ConstraintType.BLOCK_SLOT_TEACHER \
            and p.get("days") == [0]:
        db.delete(c); m += 1
    if c.constraint_type == ConstraintType.TEACHER_PREFERRED_FREE_DAY \
            and p.get("teacher_id") in math_profs and 0 in (p.get("days") or []):
        p2 = dict(p); p2["days"] = [d for d in p2["days"] if d != 0]
        c.parameters = p2; m += 1
print(f"  maths lycee : dimanche ouvert ({m} souhaits du dimanche retires)")

# --- 5. gabarit des postes vacants (לא משובץ) -------------------------------
# Leur profil imposait >=3h par jour de presence : une barrette de 5h en 3+2
# devenait impossible (le jour a 2h violait le minimum). Le minimum de
# l'ecole est 2h — on aligne.
n5 = 0
for c in db.query(Constraint).filter_by(school_id=S).all():
    if c.constraint_type != ConstraintType.TEACHER_FREE_DAY:
        continue
    p = dict(c.parameters or {})
    t = db.get(Teacher, p.get("teacher_id") or 0)
    if t is not None and 'לא משובץ' in (t.first_name or '') and p.get("min_hours_per_day") == 3:
        p["min_hours_per_day"] = 2
        c.parameters = p
        n5 += 1
print(f"  postes vacants : minimum 3h/jour -> 2h/jour ({n5} profils)")

db.commit()
print("Mises a jour du 14/08 appliquees.")
