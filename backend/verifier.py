# -*- coding: utf-8 -*-
"""Contrôle du planning contre le registre des règles. VSCHED=<id>"""
import sys, os, json
sys.path.insert(0, '.')
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")
from collections import defaultdict
from sqlalchemy.orm import sessionmaker
from app.db.base import engine
import app.models
from app.models import Group, ScheduleEntry
db = sessionmaker(bind=engine)()
S = 2
SCHED = int(os.environ.get("VSCHED", "2"))
gid2g = {g.id: g for g in db.query(Group).filter_by(school_id=S).all()}
ref = defaultdict(list)
for e in db.query(ScheduleEntry).filter_by(schedule_id=SCHED).all():
    ref[e.group_id].append((e.day_of_week, e.slot_index))

problems = []
def chk(name, ok, detail=""):
    print(("  OK   " if ok else "  ⚠️   ") + name + (f" — {detail}" if detail else ""))
    if not ok: problems.append((name, detail))

cls_grid = defaultdict(dict); tch_grid = defaultdict(list)
for gid, poss in ref.items():
    g = gid2g[gid]; su = (g.subject.name_he or '').strip()
    for d, s in poss:
        for c in g.source_classes: cls_grid[c.code].setdefault((d, s), []).append(su)
        for t in g.teachers: tch_grid[t.first_name].append((d, s, su, gid))

print("=== ÉLÈVES ===")
gaps = starts = 0; bad = []
for code, cells in cls_grid.items():
    byd = defaultdict(list)
    for (d, s) in cells: byd[d].append(s)
    for d, ss in byd.items():
        if d == 5: continue
        ss = sorted(set(ss))
        if ss[0] != 0: starts += 1; bad.append(f"{code} j{d} début P{ss[0]+1}")
        holes = [x for x in range(ss[0], ss[-1]) if x not in ss]
        if holes: gaps += len(holes); bad.append(f"{code} j{d} trous P{[h+1 for h in holes]}")
chk("0 trou élève", gaps == 0, f"{gaps} trous {bad[:4]}")
chk("Départ à P1", starts == 0, f"{starts}")

split = []
for gid, poss in ref.items():
    g = gid2g[gid]; su = (g.subject.name_he or '').strip()
    if su == 'ישיבות': continue
    byd = defaultdict(list)
    for d, s in poss: byd[d].append(s)
    for d, ss in byd.items():
        ss = sorted(ss)
        if len(ss) > 1 and any(ss[i+1]-ss[i] > 1 for i in range(len(ss)-1)):
            split.append(f"g{gid} {g.label} j{d} P{[x+1 for x in ss]}")
chk("Aucune matière (groupe) coupée dans la journée", not split, f"{len(split)}: {split[:6]}")

empty = [f"{c} j{d}" for c in cls_grid for d in range(5) if not any(k[0]==d for k in cls_grid[c])]
chk("Aucun jour vide", not empty, f"{empty[:5]}")

print("=== FINS ===")
ACAD = {'תנ"ך','תלמוד','הבעה','לשון','אזרחות','הלכה','מחשבת ישראל','היסטוריה','אנגלית','ספרות','תושב"ע'}
late = [f"{c} j{d} P{s+1} {sus}" for c, cells in cls_grid.items() for (d,s),sus in cells.items() if s>=8 and any(x in ACAD for x in sus)]
chk("Académiques ≤P8", not late, f"{late[:4]}")
hat = [f"{c} j{d} P{s+1}" for c, cells in cls_grid.items() for (d,s) in cells
       if c.split('-')[0] in ('ז','ח','ט') and s > (8 if c.startswith('ט') else 7)]
chk("חטיבה ז/ח≤P8 ט≤P9", not hat, f"{hat[:4]}")
mon = [f"{c} P{s+1}" for c, cells in cls_grid.items() for (d,s) in cells
       if d==1 and c.split('-')[0] in ('ז','ח','ט') and s > (8 if c.startswith('ט') else 6)]
chk("Lundi ז/ח≤P7 ט≤P9", not mon, f"{mon[:4]}")
for cc in ('ז-2','ח-2'):
    l = [f"j{d} P{s+1}" for (d,s) in cls_grid.get(cc,{}) if s > 5]
    chk(f"{cc} ≤P6 (P7 1×)", len(l) <= 1, f"{l}")

print("=== VENDREDI ===")
fri = defaultdict(set)
for gid, poss in ref.items():
    g = gid2g[gid]
    for d, s in poss:
        if d == 5:
            for c in g.source_classes: fri[c.code.split('-')[0]].add((g.subject.name_he or '').strip())
chk("Vendredi : une seule שכבה, que מחשבים", len(fri) <= 1 and all(v == {'מחשבים'} for v in fri.values()), f"{dict(fri)}")

print("=== מנטורים ===")
mb = []; mp = []
for gid, poss in ref.items():
    g = gid2g[gid]
    if (g.subject.name_he or '').strip() != 'מנטורים': continue
    byd = defaultdict(list)
    for d, s in poss:
        byd[d].append(s)
        if s > 2: mb.append(f"{g.label} j{d} P{s+1}")
    for d, ss in byd.items():
        if len(ss) > 1: mp.append(f"{g.label} j{d}")
chk("מנטורים P1-P3", not mb, f"{mb[:4]}")
chk("מנטורים 1h/jour", not mp, f"{len(mp)}: {mp[:5]}")

print("=== PROFS ===")
conf = []
for t, items in tch_grid.items():
    seen = defaultdict(set)
    for d, s, su, gid in items: seen[(d,s)].add(gid)
    conf += [f"{t} j{k[0]}P{k[1]+1}" for k, gs in seen.items() if len(gs) > 1]
chk("Aucun prof à 2 endroits", not conf, f"{conf[:4]}")
nofree = []; short = []; gap3 = []
for t, items in tch_grid.items():
    if 'לא משובץ' in t: continue
    days = defaultdict(set)
    for d, s, su, gid in items: days[d].add(s)
    worked = [d for d in range(5) if days.get(d)]
    if len(worked) == 5: nofree.append(t)
    for d in worked:
        ss = sorted(days[d])
        if len(ss) < 2: short.append(f"{t} j{d}")
        run = 0
        for x in range(ss[0], ss[-1]):
            run = run + 1 if x not in ss else 0
            if run >= 3: gap3.append(f"{t} j{d}"); break
chk("Congé pour tous (dim-jeu)", not nofree, f"{len(nofree)}: {nofree[:6]}")
chk("Min 2h/jour", not short, f"{len(short)}: {short[:5]}")
chk("Pas d'attente ≥3h", not gap3, f"{len(gap3)}: {sorted(set(gap3))[:6]}")

print("=== VOLUMES ===")
volbad = [f"g{gid} {gid2g[gid].label} {len(poss)}/{gid2g[gid].hours_per_week}" for gid, poss in ref.items() if len(poss) != gid2g[gid].hours_per_week]
chk("Volumes exacts", not volbad, f"{volbad[:5]}")
print(f"\n>>> {len(problems)} règle(s) en écart")
