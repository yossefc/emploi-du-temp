"""Génère une page HTML autonome pour relire l'emploi du temps.

Pensée pour la RELECTURE : on y repère d'un coup d'œil les trous, les départs
tardifs, les matières éclatées et les journées trop chargées. Une classe ou un
prof à la fois, navigation par pastilles, impression directe.

Usage :
    DATABASE_URL='sqlite:///./demo.db' python scripts/export_viewer.py [schedule_id]
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")

from sqlalchemy.orm import sessionmaker

from app.db.base import engine
import app.models  # noqa: F401
from app.models import Class, Group, Schedule, Subject, Teacher

OUT = Path(__file__).parent.parent.parent / "viewer" / "data.json"
N_PERIODS = 10
GRADE_ORDER = ["ז", "ח", "ט", "י", "יא", "יב"]
# Matières qui se donnent normalement en heures isolées : ne pas les compter
# comme « éclatées » quand elles reviennent deux fois dans la journée.
SPREAD_OK = {'חנ"ג', "מנטורים", "חינוך", 'של"ח', "כישורי חיים", "אמירים", "תקשוב"}


def main():
    db = sessionmaker(bind=engine)()
    sid = int(sys.argv[1]) if len(sys.argv) > 1 else None
    sched = (db.get(Schedule, sid) if sid else
             db.query(Schedule).order_by(Schedule.id.desc()).first())
    if sched is None:
        print("Aucun planning en base.")
        return
    sc = sched.school_id
    groups = {g.id: g for g in db.query(Group).filter_by(school_id=sc).all()}
    subjects = {s.id: s for s in db.query(Subject).filter_by(school_id=sc).all()}
    classes = db.query(Class).filter_by(school_id=sc).all()
    teachers = db.query(Teacher).filter_by(school_id=sc).all()

    cells_cls: dict[int, dict] = defaultdict(dict)
    cells_tch: dict[int, dict] = defaultdict(dict)
    for en in sched.entries:
        g = groups[en.group_id]
        subj = subjects[g.subject_id]
        key = f"{en.day_of_week},{en.slot_index}"
        who = " · ".join(t.first_name for t in g.teachers)
        color = subj.color_hex or "#94a3b8"
        for c in g.source_classes:
            cells_cls[c.id].setdefault(key, []).append(
                {"s": subj.name_he, "w": who, "c": color})
        where = ", ".join(sorted(x.code for x in g.source_classes)) or "—"
        for t in g.teachers:
            cells_tch[t.id].setdefault(key, []).append(
                {"s": subj.name_he, "w": where, "c": color})

    def audit(cells: dict, is_class: bool) -> dict:
        by_day = defaultdict(list)
        for key in cells:
            d, s = (int(x) for x in key.split(","))
            by_day[d].append(s)
        gaps = late = 0
        ends, per_day = {}, {}
        for d, sl in by_day.items():
            sl = sorted(sl)
            gaps += (sl[-1] - sl[0] + 1) - len(sl)
            if is_class and sl[0] != 0:
                late += 1
            ends[d] = sl[-1] + 1
            per_day[d] = len(sl)
        split = 0
        if is_class:
            per_subj = defaultdict(list)
            for key, items in cells.items():
                d, s = (int(x) for x in key.split(","))
                for it in items:
                    if it["s"] not in SPREAD_OK:
                        per_subj[(d, it["s"])].append(s)
            for sl in per_subj.values():
                sl = sorted(set(sl))
                if len(sl) > 1 and sl[-1] - sl[0] + 1 != len(sl):
                    split += 1
        return {"gaps": gaps, "late": late, "split": split,
                "hours": sum(per_day.values()), "days": len(by_day),
                "ends": ends, "perDay": per_day}

    data = {
        "name": sched.name,
        "generated": sched.generated_at.isoformat() if sched.generated_at else None,
        "quality": sched.quality_score or {},
        "periods": N_PERIODS,
        "entries": len(sched.entries),
        "subjects": sorted(
            ({"name": s.name_he, "color": s.color_hex or "#94a3b8"}
             for s in subjects.values()), key=lambda x: x["name"]),
        "classes": [], "teachers": [],
    }
    for c in sorted(classes, key=lambda c: (GRADE_ORDER.index(c.code.split("-")[0]),
                                            c.code)):
        cells = cells_cls.get(c.id, {})
        data["classes"].append({"id": c.id, "name": c.code, "cells": cells,
                                "audit": audit(cells, True)})
    for t in sorted(teachers, key=lambda t: t.first_name):
        cells = cells_tch.get(t.id, {})
        if not cells:
            continue
        data["teachers"].append({"id": t.id, "name": t.first_name, "cells": cells,
                                 "audit": audit(cells, False)})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print(f"✅ {OUT}  ({OUT.stat().st_size // 1024} Ko)")
    print(f"   planning #{sched.id} « {sched.name} » — {len(sched.entries)} cours")
    print(f"   {len(data['classes'])} classes · {len(data['teachers'])} profs")
    tot = data["classes"]
    print(f"   trous élèves {sum(c['audit']['gaps'] for c in tot)} · "
          f"départs tardifs {sum(c['audit']['late'] for c in tot)} · "
          f"matières éclatées {sum(c['audit']['split'] for c in tot)}")


if __name__ == "__main__":
    main()
