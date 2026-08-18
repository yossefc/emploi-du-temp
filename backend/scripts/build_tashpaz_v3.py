"""Consolidation תשפ"ז v3 — les fichiers ANNOTÉS PAR YOSSEF font autorité.

Le 10/08, Yossef a renvoyé les deux récapitulatifs (חטיבה + תיכון) après les
avoir « arrangés » à la main : heures corrigées, ט-5 intégrée aux barrettes
de שכבה ט, כהן שירה rétablie sur ז-2, חינוך et אמירים retirés de la חטיבה,
et deux colonnes ajoutées :

  F « לפצל שעות »          — pas obligé de donner les 2h ensemble (le sport,
                             c'est même mieux séparé). Déjà couvert par le
                             moteur : tout cours ≤2h est libre de s'étaler,
                             avec une légère préférence pour des jours
                             différents.
  G « אפשרי להחליף שיבוץ » — le prof peut échanger son affectation avec un
                             autre prof de la même שכבה pour la même matière.
                             Stocké dans le dataset (swap_ok), pas encore
                             exploité par le solveur.

Ces fichiers étant dérivés de mes propres exports, ils décrivent la totalité
des cours : ils REMPLACENT la fusion directeur+שחף pour la définition des
groupes. Le reste (dispos, responsabilités, réunions, questionnaire) vient
toujours des sources précédentes, via build_tashpaz_v2.

Usage : python scripts/build_tashpaz_v3.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).parent))
import build_tashpaz_v2 as v2

DATA = Path(r"D:\emploi-du-temp-projet\donnees-tashpaz")
OUT = DATA / "dataset_tashpaz_final.json"
FILES = [("תיכון", DATA / "heures_profs_yossef_1.xlsx"),
         ("חטיבה", DATA / "heures_profs_yossef_2.xlsx")]
GRADE_ORDER = ["ז", "ח", "ט", "י", "יא", "יב"]

# Corrections de saisie constatées dans les fichiers (chacune signalée dans
# le rapport pour validation) :
SUBJECT_FIX = {"ס": 'תנ"ך'}        # ligne וייס לירן — le label הקבצה le confirme
CLASS_FIX = {"ט5": "ט-5"}
# Les 23 classes réelles : toute ligne visant une autre classe (יא-4…) est
# écartée et signalée, plutôt que devinée.
VALID_CLASSES = {f"{g}-{i}" for g, n in
                 (("ז", 4), ("ח", 4), ("ט", 5), ("י", 4), ("יא", 3), ("יב", 3))
                 for i in range(1, n + 1)}
MEGAMA = v2.MEGAMA_SUBJECTS | {"תקשוב", "רובוטיקה"}

# « Le cours de français est un cours pour les עולים, on le fait à la fin »
# (Yossef 10/08) → même traitement que les autres cours עולים : hors modèle,
# placés en dernière passe. Ça retire aussi le trou de 5h qu'ils creusaient
# dans les barrettes de מגמות (3h face aux 8h de מחשבים).
POSTPONED_SUBJECTS = {"צרפתית- מגמה"}

# Cours confirmés par Yossef mais absents de ses fichiers.
# י-2, 10/08 : « elle a 2h de כישורי חיים avec la יועצת גלבוע הילה » —
# donné en réponse au mardi impossible (סבח et גוואטה absents). Porte י-2
# à 32h et lui redonne de la marge. כישורי חיים ne revit QUE pour י-2.
MANUAL_GROUPS = [
    {"teacher": "גלבוע הילה", "subject": "כישורי חיים",
     "classes": ["י-2"], "hours": 2, "seg": "תיכון"},
    # אזרחות יב-3 : la ligne de חוזה porte « - » dans le fichier ; Yossef
    # (11/08) : « marque לא משובץ, 3 שעות ».
    {"teacher": "לא משובץ 18", "subject": "אזרחות",
     "classes": ["יב-3"], "hours": 3, "seg": "תיכון", "placeholder": True},
]


def grade_of(c: str) -> str:
    return c.split("-")[0].strip()


def read_yossef(roster: set[str]):
    """Lit les deux fichiers annotés → entries + notes de lecture."""
    def resolve(raw: str) -> tuple[str, bool]:
        t = re.sub(r"\s*\(לא משובץ\)\s*", "", str(raw)).strip()
        t = re.sub(r"\s+", " ", t)
        if t.startswith("לא משובץ"):
            return (t if t != "לא משובץ" else "לא משובץ"), True
        if t in roster:
            return t, False
        # nom inversé (« שירה כהן » ↔ « כהן שירה »)
        for n in roster:
            if set(n.split()) == set(t.split()):
                return n, False
        return t, False          # nouveau nom, gardé tel quel

    entries, notes = [], []
    removed = []
    for seg, path in FILES:
        ws = openpyxl.load_workbook(path, data_only=True)["לפי מקצוע"]
        for r in list(ws.iter_rows(values_only=True))[2:]:
            if not r[0] or not r[1]:
                continue
            subj = str(r[0]).strip()
            if subj in SUBJECT_FIX:
                notes.append(f"matière « {subj} » lue comme "
                             f"{SUBJECT_FIX[subj]} ({r[1]}, {r[2]})")
                subj = SUBJECT_FIX[subj]
            teacher, is_ph = resolve(r[1])
            classes, bad_cls = [], []
            for c in str(r[2] or "").split(","):
                c = c.strip().replace(" ", "")
                if not c:
                    continue
                if c in CLASS_FIX:
                    notes.append(f"classe « {c} » lue comme {CLASS_FIX[c]} "
                                 f"({subj} / {teacher})")
                    c = CLASS_FIX[c]
                (classes if c in VALID_CLASSES else bad_cls).append(c)
            if bad_cls:
                notes.append(f"⚠ ligne ÉCARTÉE — classe inconnue "
                             f"{','.join(bad_cls)} ({subj} / {teacher}, {r[3]}ש')")
                continue
            if not classes:
                continue
            h_raw = r[3]
            if h_raw in ("-", None, ""):
                removed.append(f"{subj} / {teacher} [{','.join(classes)}]")
                continue
            try:
                hours = int(round(float(h_raw)))
            except (TypeError, ValueError):
                notes.append(f"heures illisibles « {h_raw} » — ligne ignorée "
                             f"({subj} / {teacher})")
                continue
            if subj in POSTPONED_SUBJECTS:
                removed.append(f"{subj} / {teacher} [{','.join(classes)}] "
                               f"{h_raw}h — reporté avec les cours עולים")
                continue
            entries.append({
                "teacher": teacher, "subject": subj,
                "classes": frozenset(classes), "hours": hours,
                "seg": seg,
                "coh_label": str(r[4]).strip() if r[4] else "",
                "placeholder": is_ph,
                "can_split": bool(r[5]) if len(r) > 5 else False,
                "swap_ok": r[6] is True if len(r) > 6 else False,
            })
    return entries, notes, removed


def main():
    # Sources annexes, reprises de la v2
    _, postponed_olim, responsibility = v2.read_shahaf()
    rikuz_names = set(json.loads(
        (DATA / "rikuz_shaot_parsed.json").read_text(encoding="utf-8")))
    roster = (rikuz_names - v2.DEPARTED_TEACHERS) | {"שירה לוי", "ממן חנן", "חג'בי סמדר"}

    entries, notes, removed = read_yossef(roster)
    for m in MANUAL_GROUPS:
        entries.append({"teacher": m["teacher"], "subject": m["subject"],
                        "classes": frozenset(m["classes"]), "hours": m["hours"],
                        "seg": m["seg"], "coh_label": "",
                        "placeholder": m.get("placeholder", False),
                        "can_split": True, "swap_ok": False})
        notes.append(f"ajout confirmé par Yossef : {m['subject']} "
                     f"[{','.join(m['classes'])}] {m['hours']}h — {m['teacher']}")

    # אנגלית ט liste דיין דניאל deux fois — artefact du copier-coller qui a
    # ajouté ט-5 (les quatuors de ז et ח sont אזרחי/דניאל/שטיינמיץ/ישראל).
    # Le doublon devient דיין ישראל, à valider.
    seen_pairs = set()
    for e in entries:
        key = (e["subject"], e["teacher"], e["classes"])
        if key in seen_pairs and e["teacher"] == "דיין דניאל" and e["subject"] == "אנגלית":
            e["teacher"] = "דיין ישראל"
            notes.append("⚠ אנגלית ט : le second דיין דניאל lu comme דיין ישראל "
                         "(même quatuor qu'en ז et ח) — à valider")
        else:
            seen_pairs.add(key)

    # Deux lignes de MÊME matière sur la MÊME classe sans libellé de barrette
    # = la classe est divisée en deux groupes qui tournent EN PARALLÈLE
    # (Yossef 10/08 sur היסטוריה י-3 : « c'est une הקבצה, מפצלים את הכיתה
    # ל-2 »). On leur fabrique un libellé pour qu'elles forment une cohorte.
    pairs = defaultdict(list)
    for i, e in enumerate(entries):
        if not e["coh_label"]:
            pairs[(e["seg"], e["subject"], e["classes"])].append(i)
    for (seg, subj, cls), idxs in pairs.items():
        if len(idxs) >= 2:
            label = f"הקבצה {subj} [{','.join(sorted(cls))}]"
            for i in idxs:
                entries[i]["coh_label"] = label
            notes.append(f"הקבצה intra-classe détectée : {subj} "
                         f"[{','.join(sorted(cls))}] — {len(idxs)} groupes parallèles")

    # --- Placeholders : garder les numéros de Yossef, numéroter les anonymes
    used_nums = {int(m.group(1)) for e in entries
                 if (m := re.match(r"לא משובץ (\d+)$", e["teacher"]))}
    nxt = max(used_nums, default=0)
    for e in entries:
        if e["teacher"] == "לא משובץ":
            nxt += 1
            e["teacher"] = f"לא משובץ {nxt}"

    # --- Cohortes : les lignes partageant un même libellé de הקבצה ---
    # Deux garde-fous sur les libellés, abîmés par l'édition manuelle :
    #  · le label « הקבצה הבעה » a débordé sur les lignes d'אנגלית ט → la
    #    matière fait partie de la clé, une barrette ne mélange pas אנגלית
    #    et הבעה ;
    #  · les lignes de מגמות portent des variantes du même label → toutes
    #    les מגמות d'une même שכבה forment UNE barrette, comme avant.
    def coh_key(e):
        if not e["coh_label"]:
            return None
        if e["subject"] in MEGAMA:
            grades = frozenset(grade_of(c) for c in e["classes"])
            return (e["seg"], "מגמות", grades)
        return (e["seg"], e["subject"], e["coh_label"])

    by_label = defaultdict(list)
    for i, e in enumerate(entries):
        k = coh_key(e)
        if k is not None:
            by_label[k].append(i)

    absorbed, cohort_of, cohorts = [], {}, []
    for key, idxs in by_label.items():
        if len(idxs) < 2:
            continue          # libellé orphelin → cours autonome
        by_teacher = defaultdict(list)
        for i in idxs:
            by_teacher[entries[i]["teacher"]].append(i)
        kept, dropped = [], set()
        for t, tis in by_teacher.items():
            tis.sort(key=lambda i: (-len(entries[i]["classes"]), -entries[i]["hours"]))
            kept.append(tis[0])
            for i in tis[1:]:
                dropped.add(i)
                absorbed.append(f"{t} — {entries[i]['subject']} "
                                f"[{','.join(sorted(entries[i]['classes']))}] "
                                f"{entries[i]['hours']}h absorbé (doublon dans {key[1]})")
        if len(kept) < 2:
            continue
        cls_union = sorted(set().union(*(entries[i]["classes"] for i in kept)))
        cid = len(cohorts)
        label = (entries[kept[0]]["coh_label"] if key[1] != "מגמות"
                 else f"הקבצה מגמות [{','.join(cls_union)}]")
        cohorts.append({"label": label[:190], "classes": cls_union,
                        "entries": kept,
                        "same_subject": len({entries[i]["subject"] for i in kept}) == 1})
        for i in kept:
            cohort_of[i] = cid
        for i in dropped:
            entries[i]["hours"] = 0        # neutralisé, filtré plus bas

    keep = [i for i, e in enumerate(entries) if e["hours"] > 0]
    remap = {old: new for new, old in enumerate(keep)}
    entries = [entries[i] for i in keep]
    cohort_of = {remap[i]: c for i, c in cohort_of.items() if i in remap}
    for c in cohorts:
        c["entries"] = [remap[i] for i in c["entries"] if i in remap]

    # --- Référentiels ---
    all_classes = sorted({c for e in entries for c in e["classes"]},
                         key=lambda c: (GRADE_ORDER.index(grade_of(c)), c))
    all_subjects = sorted({e["subject"] for e in entries})
    real_teachers = sorted({e["teacher"] for e in entries if not e["placeholder"]})
    placeholders = sorted({e["teacher"] for e in entries if e["placeholder"]})

    # Réunions (rikuz) — participants hors service ajoutés comme profs
    meetings = []
    for m in v2.read_meetings():
        parts = [p for p in m["participants"] if p not in v2.DEPARTED_TEACHERS]
        if len(parts) >= 2:
            meetings.append({**m, "participants": parts})
    meeting_only = sorted({p for m in meetings for p in m["participants"]}
                          - set(real_teachers) - set(placeholders))
    real_teachers = sorted(set(real_teachers) | set(meeting_only))

    # Dispos + questionnaire
    shahaf_raw = json.loads((DATA / "tashpaz_dataset.json").read_text(encoding="utf-8"))
    directeur_old = json.loads(
        (DATA / "dataset_hativa_directeur.json").read_text(encoding="utf-8"))
    dispo = {}
    for t in shahaf_raw.get("teachers", []):
        if t.get("unavailable_periods"):
            dispo[t["name"]] = t["unavailable_periods"]
    for t in directeur_old.get("teachers", []):
        n = t.get("name_shahaf")
        if n and n not in dispo and t.get("unavailable_periods"):
            dispo[n] = t["unavailable_periods"]
    shealon, shealon_unknown = v2.read_shealon(real_teachers)

    DAY = {"sunday": 0, "monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4}
    teachers_out, n_dispo = [], 0
    for name in real_teachers:
        blocks = []
        for p in dispo.get(name, []):
            d, per = DAY.get(p.get("day")), p.get("period")
            if d is not None and isinstance(per, int) and 1 <= per <= v2.N_PERIODS:
                blocks.append({"day": d, "slot": per - 1})
        if blocks:
            n_dispo += 1
        sh = shealon.get(name, {})
        teachers_out.append({"name": name, "blocked": blocks,
                             "responsibility_hours": responsibility.get(name, 0),
                             "preferred_free_days": sh.get("preferred_free_days", []),
                             "role": sh.get("role", ""),
                             "answered_questionnaire": bool(sh)})

    groups_out = [{
        "subject": e["subject"], "teacher": e["teacher"],
        "placeholder": e["placeholder"],
        "classes": sorted(e["classes"]), "hours": e["hours"],
        "cohort": cohort_of.get(i),
        "can_split": e["can_split"], "swap_ok": e["swap_ok"],
    } for i, e in enumerate(entries)]

    out = {
        "meta": {
            "school": 'אמי"ת בר אילן נתניה', "year": 'תשפ"ז (2026-2027)',
            "source": "קבצי יוסף 10/08 (שעות מתוקנות ידנית) + שחף (זמינות, ישיבות)",
            "week_days": 5, "periods_per_day": v2.N_PERIODS,
            "n_classes": len(all_classes), "n_subjects": len(all_subjects),
            "n_teachers": len(real_teachers), "n_placeholders": len(placeholders),
            "n_groups": len(groups_out), "n_cohorts": len(cohorts),
            "n_teachers_with_dispos": n_dispo,
            "n_meetings": len(meetings),
            "n_questionnaire_answers": len(shealon),
            "n_can_split": sum(1 for g in groups_out if g["can_split"]),
            "n_swap_ok": sum(1 for g in groups_out if g["swap_ok"]),
            "n_postponed_olim": len(postponed_olim),
        },
        "postponed_olim": [{"teacher": p["teacher"], "subject": p["subject"],
                            "classes": sorted(p["classes"]), "hours": p["hours"]}
                           for p in postponed_olim],
        "meetings": meetings,
        "classes": all_classes, "subjects": all_subjects,
        "teachers": teachers_out, "placeholders": placeholders,
        "groups": groups_out,
        "cohorts": [{"label": c["label"], "classes": c["classes"],
                     "n_groups": len(c["entries"]),
                     "same_subject": c["same_subject"]} for c in cohorts],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    p = lambda *a: print(*a, file=sys.stderr)
    p('=== Consolidation תשפ"ז v3 (fichiers Yossef) ===')
    for k, val in out["meta"].items():
        p(f"  {k}: {val}")
    if notes:
        p(f"\n=== {len(notes)} corrections de lecture — à valider ===")
        for n in notes:
            p(f"  • {n}")
    if removed:
        p(f"\n=== {len(removed)} cours retirés (heures « - ») ===")
        for r in removed:
            p(f"  • {r}")
    if absorbed:
        p(f"\n=== {len(absorbed)} doublons absorbés ===")
        for a in absorbed:
            p(f"  • {a}")
    if meeting_only:
        p(f"\n=== participants de réunion sans cours : {', '.join(meeting_only)} ===")
    if shealon_unknown:
        p(f"=== questionnaire non rattaché : "
          f"{', '.join(x['form_name'] for x in shealon_unknown)} ===")

    p("\n=== Charge hebdo par classe ===")
    env = defaultdict(int)
    for i, e in enumerate(entries):
        ci = cohort_of.get(i)
        if ci is not None:
            env[ci] = max(env[ci], e["hours"])
    load, seen = defaultdict(int), defaultdict(set)
    for i, e in enumerate(entries):
        ci = cohort_of.get(i)
        for c in e["classes"]:
            if ci is not None:
                if ci in seen[c]:
                    continue
                seen[c].add(ci)
                load[c] += env[ci]
            else:
                load[c] += e["hours"]
    for c in all_classes:
        flag = "  ⚠ > capacité P9 (42h)" if (grade_of(c) in ("ז", "ח", "ט")
                                             and load[c] > 42) else ""
        cap50 = "  ⚠ SURCHARGE" if load[c] > 50 else ""
        p(f"  {c:<7} {load[c]}h{flag}{cap50}")


if __name__ == "__main__":
    main()
