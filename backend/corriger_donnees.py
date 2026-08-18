# -*- coding: utf-8 -*-
"""Corrections de donnees demandees par Yossef le 13/08 (soir)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")
from sqlalchemy.orm import sessionmaker
from app.db.base import engine
import app.models
from app.models import (Group, Teacher, TimeSlot, Constraint, ConstraintType,
                        ConstraintPriority, ConstraintOriginRole, ParallelCohort)
db = sessionmaker(bind=engine)()
S = 2

def T(name):
    for t in db.query(Teacher).filter_by(school_id=S).all():
        if name in f"{t.first_name or ''} {t.last_name or ''}":
            return t

# 1) מולאורי n'a rien a faire en ח-4 -> suppression du groupe
g = next((x for x in db.query(Group).filter_by(school_id=S).all()
          if x.label == 'מתמטיקה ח-4 (תגבור)'), None)
if g:
    db.delete(g); print("  - supprime : מתמטיקה ח-4 (תגבור) מולאורי 2h")

# 2) אזרחות ט-1 -> הרב יוני ספר   |   אזרחות ט-5 -> מימון נתנאל
for gid, nom in ((450, 'ספר מוריס יוני'), (453, 'מימון נתנאל')):
    grp = db.get(Group, gid)
    if grp:
        old = [t.first_name for t in grp.teachers]
        grp.teachers.clear(); grp.teachers.append(T(nom))
        print(f"  ~ אזרחות {[c.code for c in grp.source_classes]} : {old} -> {nom}")

# 3) פרטוק et בגו se COMPLETENT en אלקטרוניקה י (heures differentes, memes
#    eleves) : ils ne sont pas deux filieres paralleles. On sort בגו de la
#    cohorte pour qu'il puisse se placer a d'autres heures que פרטוק.
g331 = db.get(Group, 331)
if g331 and g331.parallel_cohort_id is not None:
    g331.parallel_cohort_id = None
    g331.label = 'אלקטרוניקה י-1+י-3+י-4 (בגו)'
    print("  ~ אלקטרוניקה י : בגו decouple de פרטוק (ils se completent)")

# 4) בגו peut aller jusqu'a P11 son mercredi -> 11e creneau ce jour-la
if not db.query(TimeSlot).filter_by(school_id=S, day_of_week=3, slot_index=10).first():
    ref = db.query(TimeSlot).filter_by(school_id=S, day_of_week=3, slot_index=9).first()
    db.add(TimeSlot(school_id=S, day_of_week=3, slot_index=10,
                    start_time=ref.start_time, end_time=ref.end_time))
    db.flush()
    print("  + P11 ouvert le mercredi")
    # ferme P11 pour TOUT LE MONDE sauf les groupes de בגו
    bego = T('בגו')
    bego_gids = {x.id for x in db.query(Group).filter_by(school_id=S).all()
                 if any(t.id == bego.id for t in x.teachers)}
    n = 0
    for grp in db.query(Group).filter_by(school_id=S).all():
        if grp.id in bego_gids:
            continue
        db.add(Constraint(
            school_id=S, constraint_type=ConstraintType.BLOCK_SLOT_GROUP,
            priority=ConstraintPriority.HARD,
            parameters={"days": [3], "slot_indices": [10], "target_id": grp.id},
            origin_role=ConstraintOriginRole.SCHOOL_ADMIN,
            origin_description='P11 רביעי — רק לבגו (יוסף 13/08)', is_active=True))
        n += 1
    print(f"    ({n} groupes bloques en P11, seul בגו y a droit)")

# 5) ממן חנן : dimanche + mercredi (inchange). Correction du 13/08 soir —
#    c'est בגו, pas ממן, qui remplit son mercredi jusqu'a P11. On repare donc
#    une eventuelle execution precedente de ce script.
maman = T('ממן')
if maman:
    mauvais = [c for c in db.query(Constraint).filter_by(school_id=S).all()
               if 'ממן חנן — רק יום רביעי' in (c.origin_description or "")]
    if mauvais:
        for c in mauvais:
            db.delete(c)
        for d in (1, 2, 4):          # ferme lundi, mardi, jeudi
            db.add(Constraint(
                school_id=S, constraint_type=ConstraintType.BLOCK_SLOT_TEACHER,
                priority=ConstraintPriority.HARD,
                parameters={"days": [d], "slot_indices": list(range(11)),
                            "target_id": maman.id},
                origin_role=ConstraintOriginRole.TEACHER,
                origin_description='ממן חנן — ראשון ורביעי בלבד', is_active=True))
        print("  ממן חנן : retabli sur dimanche + mercredi")
    # P11 reste ferme pour lui (seul בגו y a droit)
    maman_gids = {x.id for x in db.query(Group).filter_by(school_id=S).all()
                  if any(t.id == maman.id for t in x.teachers)}
    for gid in maman_gids:
        existe = any('P11 רביעי' in (c.origin_description or "")
                     and (c.parameters or {}).get("target_id") == gid
                     for c in db.query(Constraint).filter_by(school_id=S).all())
        if not existe:
            db.add(Constraint(
                school_id=S, constraint_type=ConstraintType.BLOCK_SLOT_GROUP,
                priority=ConstraintPriority.HARD,
                parameters={"days": [3], "slot_indices": [10], "target_id": gid},
                origin_role=ConstraintOriginRole.SCHOOL_ADMIN,
                origin_description='P11 רביעי — רק לבגו (יוסף 13/08)', is_active=True))

# 6) רקנטי אליהו : ne travaille que dimanche et lundi (Yossef 13/08)
rek = T('רקנטי')
if rek:
    for d in (2, 3, 4):
        deja_d = any(
            (c.parameters or {}).get("target_id") == rek.id
            and (c.parameters or {}).get("days") == [d]
            and len((c.parameters or {}).get("slot_indices", [])) >= 10
            for c in db.query(Constraint).filter_by(school_id=S).all()
            if c.constraint_type == ConstraintType.BLOCK_SLOT_TEACHER)
        if deja_d:
            continue
        db.add(Constraint(
            school_id=S, constraint_type=ConstraintType.BLOCK_SLOT_TEACHER,
            priority=ConstraintPriority.HARD,
            parameters={"days": [d], "slot_indices": list(range(11)),
                        "target_id": rek.id},
            origin_role=ConstraintOriginRole.TEACHER,
            origin_description='רקנטי אליהו — רק ראשון ושני (יוסף 13/08)', is_active=True))
    print("  רקנטי אליהו : uniquement dimanche et lundi")

db.commit()
print("Donnees corrigees.")
