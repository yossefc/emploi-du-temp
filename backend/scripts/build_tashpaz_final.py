"""Consolidation finale תשפ"ז — produit dataset_tashpaz_final.json.

Sources (D:/emploi-du-temp-projet/donnees-tashpaz/) :
- rikuz_shaot_parsed.json      : affectations שחף école complète (PRIMAIRE)
- dataset_hativa_directeur.json: autorité חטיבה → apporte ט-5
- tashpaz_dataset.json         : dispos profs (unavailable_periods)

Règles appliquées (voir tashpaz-consolidation-decisions.md + contraintes-tashpaz.md) :
- Semaine א'-ה' (5 jours), 11 périodes numérotées P1-P11 (slot 0-10)
- Matières hors grille exclues (שהייה, פרטני, ישיבות, השתלמות…)
- Ligne multi-classes = un cours commun ; même (matière, classes) chez 2+
  profs = barrette (cohorte) ; même prof en double → fusion (hours = max)
- מגמות lycée (מחשבים/אלקטרוניקה/פיזיקה/רובוטיקה/צרפתית/תעבורה) partageant
  le même set de classes → UNE cohorte commune (elles tournent ensemble)
- "לא משובץ" → prof placeholder unique par cours
- ט-5 ajoutée depuis le dataset directeur
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

DATA = Path(r"D:\emploi-du-temp-projet\donnees-tashpaz")
OUT = DATA / "dataset_tashpaz_final.json"

EXCLUDE_SUBJECTS = {
    "שהייה", "פרטני", "השתלמות", "קבלת הורים", "תקשוב", "השכלה כללית",
    "ישיבת הנהלה", "ישיבת הנהלה חטיבתית", "ישיבת מחנכים", "ישיבת מנטורים",
    "ישיבת צוות", "ישיבת רכזים", "מורת שילוב", "שעות שילוב",
}
MEGAMA_SUBJECTS = {"מחשבים", "אלקטרוניקה", "פיזיקה", "רובוטיקה", "צרפתית- מגמה", "תעבורה"}
LYCEE_PREFIXES = ("י-", "יא-", "יב-")

def grade_of(class_code: str) -> str:
    prefix = class_code.split("-")[0].strip()
    return {"ז": "G7", "ח": "G8", "ט": "G9", "י": "G10", "יא": "G11", "יב": "G12"}.get(prefix, "G7")


def main():
    rikuz = json.loads((DATA / "rikuz_shaot_parsed.json").read_text(encoding="utf-8"))
    directeur = json.loads((DATA / "dataset_hativa_directeur.json").read_text(encoding="utf-8"))
    shahaf = json.loads((DATA / "tashpaz_dataset.json").read_text(encoding="utf-8"))

    # ---- 1. Lignes de cours filtrées ----
    # entry = {teacher, subject, classes(frozenset), hours}
    entries = []
    postponed_olim = []   # cours עולים : placés À LA FIN (décision Yossef 06/08)
    for tname, t in rikuz.items():
        for l in t["lines"]:
            subj = l["subject"].strip()
            if subj in EXCLUDE_SUBJECTS:
                continue
            classes = [c.strip() for c in l["classes"] if c.strip()]
            if not classes:
                continue
            if subj.endswith(" עולים"):
                postponed_olim.append({
                    "teacher": tname, "subject": subj,
                    "classes": sorted(classes), "hours": int(round(l["hours"])),
                })
                continue
            entries.append({
                "teacher": tname, "subject": subj,
                "classes": frozenset(classes), "hours": int(round(l["hours"])),
            })

    # ---- 2. Fusion doublons même prof / même (matière, classes) → hours=max ----
    merged: dict = {}
    for e in entries:
        key = (e["teacher"], e["subject"], e["classes"])
        if key in merged:
            merged[key] = max(merged[key], e["hours"])
        else:
            merged[key] = e["hours"]
    entries = [
        {"teacher": t, "subject": s, "classes": c, "hours": h}
        for (t, s, c), h in merged.items()
    ]

    # ---- 3. ט-5 depuis le dataset directeur ----
    dir_teachers = {t["code"]: t for t in directeur["teachers"]}
    tet5_added = 0
    for g in directeur["groups"]:
        if g.get("class") != "ט5" or g.get("hours_per_week", 0) <= 0:
            continue
        tcode = g.get("teacher")
        tinfo = dir_teachers.get(tcode, {})
        tname = tinfo.get("name_shahaf") or tinfo.get("name_directeur") or "לא משובץ"
        entries.append({
            "teacher": tname, "subject": g["subject"].strip(),
            "classes": frozenset({"ט-5"}), "hours": int(round(g["hours_per_week"])),
        })
        tet5_added += 1

    # ---- 4. Placeholders pour לא משובץ ----
    placeholder_n = 0
    for e in entries:
        if e["teacher"] == "לא משובץ":
            placeholder_n += 1
            e["teacher"] = f"לא משובץ {placeholder_n}"
            e["placeholder"] = True
            # Artefact données : ligne מנטורים agrégée à 15h sur poste non
            # pourvu — la réalité (dataset directeur) = 3h. Cap + flag.
            if e["hours"] > 8:
                print(f"  ⚠ CAP {e['subject']} {sorted(e['classes'])} "
                      f"{e['hours']}h → 3h (artefact, à valider)", file=sys.stderr)
                e["hours"] = 3

    # ---- 5. Cohortes par UNION-FIND ----
    # Règle : deux cours appartiennent au même lien s'ils ont
    #   (a) même matière (ou tous deux matière de מגמה),
    #   (b) même(s) שכבה(s),
    #   (c) des classes qui se RECOUVRENT.
    # C'est ce qui fusionne "תלמוד ז [ז-1,ז-3,ז-4]" et "תלמוד ז [ז-1,ז-2,ז-3]"
    # en UNE barrette שכבה-wide (sinon les heures des classes doublent).

    def grades_of(class_set):
        return frozenset(c.split("-")[0].strip() for c in class_set)

    def bucket(subject):
        if subject in MEGAMA_SUBJECTS:
            return "מגמות"
        # Les cours עולים tournent EN PARALLÈLE du cours normal (les élèves
        # olim sortent de la classe) → même lien que la matière de base.
        if subject.endswith(" עולים"):
            return subject[: -len(" עולים")].strip()
        return subject

    parent = list(range(len(entries)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    by_key = defaultdict(list)
    for i, e in enumerate(entries):
        by_key[(bucket(e["subject"]), grades_of(e["classes"]))].append(i)

    for key, idxs in by_key.items():
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                i, j = idxs[a], idxs[b]
                if entries[i]["classes"] & entries[j]["classes"]:
                    union(i, j)

    comp: dict[int, list[int]] = defaultdict(list)
    for i in range(len(entries)):
        comp[find(i)].append(i)

    # ÉJECTION : un même prof ne peut pas avoir 2 groupes SIMULTANÉS dans un
    # lien (clash avec lui-même). On garde son groupe le plus large dans le
    # lien, les autres deviennent des cours indépendants (séquentiels).
    ejected_report = []
    cohort_of_entry: dict[int, int] = {}
    final_cohorts: list[dict] = []
    for root, idxs in comp.items():
        if len(idxs) < 2:
            continue
        by_teacher = defaultdict(list)
        for i in idxs:
            by_teacher[entries[i]["teacher"]].append(i)
        kept = []
        for t, tis in by_teacher.items():
            if len(tis) == 1:
                kept.extend(tis)
            else:
                tis_sorted = sorted(tis, key=lambda i: (-len(entries[i]["classes"]),
                                                          -entries[i]["hours"]))
                kept.append(tis_sorted[0])
                for i in tis_sorted[1:]:
                    ejected_report.append(
                        f"{t} — {entries[i]['subject']} "
                        f"[{','.join(sorted(entries[i]['classes']))}] {entries[i]['hours']}h"
                    )
        if len(kept) < 2:
            continue
        class_union = sorted(set().union(*(entries[i]["classes"] for i in kept)))
        subjects_in = sorted({entries[i]["subject"] for i in kept})
        same_subject = len(subjects_in) == 1
        cid = len(final_cohorts)
        final_cohorts.append({
            "label": f"הקבצה {'+'.join(subjects_in)} [{','.join(class_union)}]"[:190],
            "classes": class_union,
            "entries": kept,
            "same_subject": same_subject,
        })
        for i in kept:
            cohort_of_entry[i] = cid

    if ejected_report:
        print(f"\n=== {len(ejected_report)} cours ÉJECTÉS des liens "
              f"(même prof en double → séquentiel) — À VALIDER ===", file=sys.stderr)
        for line in ejected_report:
            print(f"  • {line}", file=sys.stderr)

    # ---- 6. Référentiels ----
    all_classes = sorted({c for e in entries for c in e["classes"]})
    all_subjects = sorted({e["subject"] for e in entries})
    real_teachers = sorted({e["teacher"] for e in entries if not e.get("placeholder")})
    placeholders = sorted({e["teacher"] for e in entries if e.get("placeholder")})

    # Dispos profs : union tashpaz_dataset (prioritaire) puis directeur (name_shahaf)
    dispo_by_name = {}
    for t in shahaf.get("teachers", []):
        if t.get("unavailable_periods"):
            dispo_by_name[t["name"]] = t["unavailable_periods"]
    for t in directeur.get("teachers", []):
        n = t.get("name_shahaf")
        if n and n not in dispo_by_name and t.get("unavailable_periods"):
            dispo_by_name[n] = t["unavailable_periods"]

    DAY_IDX = {"sunday": 0, "monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4}
    teachers_out = []
    n_dispo = 0
    for name in real_teachers:
        periods = dispo_by_name.get(name, [])
        blocks = []
        for p in periods:
            d = DAY_IDX.get(p.get("day"))
            per = p.get("period")
            if d is None or not isinstance(per, int) or not (1 <= per <= 11):
                continue
            blocks.append({"day": d, "slot": per - 1})
        if blocks:
            n_dispo += 1
        teachers_out.append({"name": name, "blocked": blocks})

    groups_out = []
    for i, e in enumerate(entries):
        groups_out.append({
            "subject": e["subject"],
            "teacher": e["teacher"],
            "placeholder": bool(e.get("placeholder")),
            "classes": sorted(e["classes"]),
            "hours": e["hours"],
            "cohort": cohort_of_entry.get(i),
        })

    out = {
        "meta": {
            "school": 'אמי"ת בר אילן נתניה',
            "year": 'תשפ"ז (2026-2027)',
            "week_days": 5, "periods_per_day": 11,
            "n_classes": len(all_classes), "n_subjects": len(all_subjects),
            "n_teachers": len(real_teachers), "n_placeholders": len(placeholders),
            "n_groups": len(groups_out), "n_cohorts": len(final_cohorts),
            "n_teachers_with_dispos": n_dispo, "tet5_groups": tet5_added,
            "n_postponed_olim": len(postponed_olim),
        },
        "postponed_olim": postponed_olim,
        "classes": all_classes,
        "subjects": all_subjects,
        "teachers": teachers_out,
        "placeholders": placeholders,
        "groups": groups_out,
        "cohorts": [{"label": c["label"], "classes": c["classes"],
                     "n_groups": len(c["entries"]),
                     "same_subject": c["same_subject"]} for c in final_cohorts],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    m = out["meta"]
    print("=== Consolidation תשפ\"ז ===", file=sys.stderr)
    for k, v in m.items():
        print(f"  {k}: {v}", file=sys.stderr)

    # ---- Contrôle de faisabilité : charge par classe ----
    # Un lien (cohorte) occupe la classe pendant les heures de son ENVELOPPE
    # (le max des groupes) — compté UNE fois. Cours hors cohorte : leurs heures.
    print("\n=== Charge hebdo par classe (max 55 = 5j × 11p) ===", file=sys.stderr)
    class_load = defaultdict(int)
    for ci, c in enumerate(final_cohorts):
        env = max(entries[i]["hours"] for i in c["entries"])
        for cl in c["classes"]:
            class_load[cl] += env
    for i, e in enumerate(entries):
        if i not in cohort_of_entry:
            for cl in e["classes"]:
                class_load[cl] += e["hours"]
    for cl in sorted(class_load):
        flag = "  ⚠ SURCHARGE" if class_load[cl] > 52 else ""
        print(f"  {cl:<7} {class_load[cl]}h{flag}", file=sys.stderr)


if __name__ == "__main__":
    main()
