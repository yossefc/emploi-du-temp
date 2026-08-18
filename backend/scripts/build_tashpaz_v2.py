"""Consolidation תשפ"ז v2 — le שיבוץ du DIRECTEUR fait autorité pour la חטיבה.

Produit dataset_tashpaz_final.json (même format que build_tashpaz_final.py).

Partage des rôles entre les deux sources
----------------------------------------
שיבוצי תשפז חטב.xlsx (directeur), feuille « שיבוצי מורים ומקצועות לפי כיתות » :
    → AUTORITÉ sur les 12 matières académiques de la חטיבה : qui enseigne
      quoi, dans quelle classe, combien d'heures. Contient ט-5 et les vrais
      volumes des classes חנ"מ. Contient aussi les 2 מנטורים par classe.
    → MAIS il présente les הקבצות classe par classe, et il a des trous
      (ז-4, ח-4 : plusieurs matières laissées vides).

rikuz שחף :
    → AUTORITÉ sur la STRUCTURE DES LIENS : quelles classes tournent
      ensemble dans une barrette. C'est ce qui comble les trous du directeur
      (תנ"ך ז : le directeur ne remplit que ז-1/ז-3, שחף dit que le lien
      couvre ז-1+ז-3+ז-4 → ז-4 récupère ses heures).
    → SEULE source pour חינוך / שיח בוקר / כישורי חיים et pour tout le lycée.
    → SEULE source pour les disponibilités des profs.

Corrections apportées par rapport à build_tashpaz_final.py
----------------------------------------------------------
1. מנטורים : présent sur les 13 classes (2 mentors × 3h) et non plus sur
   la seule ז-1 avec un volume agrégé de 15h.
2. ט-5 complète (אזרחות, אנגלית, עברית, תושב"ע qui manquaient).
3. Lignes redondantes de שחף supprimées : quand un prof enseigne la même
   matière sur [ט-1,ט-3,ט-4] ET sur [ט-3], la seconde est un détail de la
   première, pas un cours en plus (c'était la cause des חנ"ג 6h, היסטוריה 4h…).
4. Classes חנ"מ protégées : une barrette de שחף n'aspire pas ז-2/ח-2/ט-2
   si le directeur n'y a pas explicitement mis ce prof.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl

DATA = Path(r"D:\emploi-du-temp-projet\donnees-tashpaz")
XLSX = DATA / "shibutz_directeur_hatab_v2.xlsx"
SHEET = "שיבוצי מורים ומקצועות לפי כיתות"
OUT = DATA / "dataset_tashpaz_final.json"

EXCLUDE_SUBJECTS = {
    # תקשוב N'EST PAS ici : c'est une vraie matière (60 créneaux en תשפ"ו),
    # classée par erreur comme ligne administrative. Voir MANUAL_GROUPS.
    "שהייה", "פרטני", "השתלמות", "קבלת הורים", "השכלה כללית",
    "ישיבת הנהלה", "ישיבת הנהלה חטיבתית", "ישיבת מחנכים", "ישיבת מנטורים",
    "ישיבת צוות", "ישיבת רכזים", "מורת שילוב", "שעות שילוב",
    # תפילה a lieu AVANT la première période (« heure 0 », Yossef 06/08) :
    # elle est hors grille, donc hors modèle.
    "תפילה",
    # « שיח בוקר ומנטורים c'est la même chose » (Yossef 07/08). שחף les liste
    # sous deux noms, avec les MÊMES profs sur les mêmes classes (vérifié :
    # ז-1 אלמו+דיין, ז-3 אבקסר+עטיה, ז-4 ברגו+דהן, ח-1 הראל+יפרח,
    # ח-3 אברהמי+מקואייה, ח-4 איפרגן+אלחדד). Les garder tous les deux comptait
    # le cours en double (3h + 3h). On ne garde que מנטורים, dont le שיבוץ
    # directeur fait autorité.
    "שיח בוקר",
    # Pas demandée pour תשפ"ז (Yossef 09/08). Elle ne figure que dans שחף,
    # jamais dans le שיבוץ du directeur — 32h sur 15 classes retirées.
    # ⚠ חינוך est dans le même cas (שחף seul, 1h par classe) mais reste
    #   dans le modèle : c'est l'heure de vie de classe, à confirmer.
    "כישורי חיים",
}
MEGAMA_SUBJECTS = {"מחשבים", "אלקטרוניקה", "פיזיקה", "רובוטיקה",
                   "צרפתית- מגמה", "תעבורה", "תקשוב"}

# Cours absents des deux fichiers sources mais confirmés par l'école.
# ממן חנן / תקשוב (capture שחף envoyée par Yossef le 07/08) : 4h sur la שכבה י
# et 7h sur la שכבה יב. Les class-sets suivent ceux de la barrette de מגמות
# de leur שכבה — la capture était tronquée (« י-1, י-3,… »), donc À CONFIRMER.
MANUAL_GROUPS = [
    {"teacher": "ממן חנן", "subject": "תקשוב",
     "classes": ["י-1", "י-3", "י-4"], "hours": 4},
    {"teacher": "ממן חנן", "subject": "תקשוב",
     "classes": ["יב-1", "יב-2", "יב-3"], "hours": 7},
]

# Lignes du rikuz qui ne sont pas des cours mais du temps de présence :
# elles ne vont pas dans la grille, mais elles comptent pour savoir combien de
# jours le prof est à l'école (barème ימי עבודה).
NON_FRONTAL_SUBJECTS = {
    "שהייה", "פרטני", "השתלמות", "קבלת הורים", "השכלה כללית",
    "ישיבת הנהלה", "ישיבת הנהלה חטיבתית", "ישיבת מחנכים", "ישיבת מנטורים",
    "ישיבת צוות", "ישיבת רכזים", "מורת שילוב", "שעות שילוב",
}

# Profs qui ne reviennent pas en תשפ"ז : leurs cours deviennent des postes à
# pourvoir (לא משובץ) pour rester visibles dans la planification.
# יהב עידן : parti, l'école cherche un remplaçant (Yossef, 07/08). Il était
# מחנך de י-3 (תלמוד 8h + תנ"ך 3h + חינוך 1h).
DEPARTED_TEACHERS = {"יהב עידן"}

HATIVA_GRADES = ("ז", "ח", "ט")
SPECIAL_ED = {"ז-2", "ח-2", "ט-2"}          # חינוך מיוחד : jamais aspirées

# Matières de vie scolaire : absentes du שיבוץ directeur, donc connues de שחף
# seul — et le rikuz y agrège des volumes invraisemblables (כישורי חיים avec
# אלמו רפאל à 9h/sem sur ט-1+ט-3+ט-4, תפילה 5h sur יב-1). Comme l'enveloppe
# d'une barrette prend le max, ces valeurs poussaient ט-1/ט-3/ט-4 à 50h sur
# 55 créneaux et rendaient le modèle infaisable. Plafond prudent + rapport,
# À FAIRE VALIDER PAR L'ÉCOLE.
VIE_SCOLAIRE = {"כישורי חיים", "חינוך"}
VIE_MAX_HOURS = 3

# 10 périodes de cours par jour (P1-P10) : structure réelle de תשפ"ו.
N_PERIODS = 10

# Vocabulaire : le directeur et שחף nomment 2 matières différemment.
# On garde les noms שחף (utilisés aussi au lycée) pour ne pas créer de doublon.
DIR2SHAHAF = {"עברית": "הבעה", 'תושב"ע': "תלמוד"}


SHEALON = DATA / "shealon_morim_tashpaz.xlsx"
SHEALON_SHEET = "תגובות לטופס 1"
# Variantes d'orthographe entre le formulaire et le rikuz שחף.
SHEALON_ALIAS = {
    "שטינמץ יעל": "שטיינמיץ יעל", "אוולייה דבורה": "טוולייה דבורה הוגט",
    "אבסקר ידידיה": "אבקסר ידידיה", "ויצמן מוריה": "וייצמן מוריה",
}
FORM_DAY = {"יום א": 0, "יום ב": 1, "יום ג": 2, "יום ד": 3, "יום ה": 4}


def read_meetings() -> list[dict]:
    """Les ישיבות telles que le rikuz שחף les décrit.

    Yossef, 07/08 : « regarde comment étaient les réunions l'année dernière,
    ce sont les mêmes ». Elles n'apparaissent pas dans l'emploi du temps par
    classe (une réunion n'a pas d'élèves) mais chaque participant porte une
    ligne « ישיבת … » dans le rikuz, avec sa durée. On en tire directement la
    composition réelle et le nombre d'heures, au lieu de les deviner.

    ישיבת צוות est écartée : 33 participants, c'est l'agrégat des réunions
    d'équipe disciplinaires, pas une réunion unique.
    """
    rikuz = json.loads((DATA / "rikuz_shaot_parsed.json").read_text(encoding="utf-8"))
    by_meeting: dict[str, dict[str, int]] = defaultdict(dict)
    for tname, t in rikuz.items():
        for l in t["lines"]:
            s = l["subject"].strip()
            if s.startswith("ישיב") and s != "ישיבת צוות":
                h = int(round(l["hours"]))
                by_meeting[s][tname] = max(by_meeting[s].get(tname, 0), h)
    out = []
    for label, people in by_meeting.items():
        parts = sorted(n for n in people if n != "לא משובץ")
        if len(parts) < 2:
            continue
        hours = max(people.values())
        out.append({"label": label, "participants": parts, "hours": hours})
    return sorted(out, key=lambda m: -len(m["participants"]))


def read_shealon(known: list[str]) -> tuple[dict, list[dict]]:
    """Questionnaire תשפ"ז : jour de congé souhaité (1er/2e/3e choix) + rôle.

    C'est la seule source de demandes datées de CETTE année ; les blocages
    hérités de תשפ"ו restent à confirmer. Retourne (par prof, non reconnus).
    """
    if not SHEALON.exists():
        return {}, []
    ws = openpyxl.load_workbook(SHEALON, data_only=True)[SHEALON_SHEET]
    out, unknown = {}, []
    for r in list(ws.iter_rows(values_only=True))[1:]:
        last, first = (r[1] or "").strip(), (r[2] or "").strip()
        if not last and not first:
            continue
        full = f"{last} {first}".strip()
        name = SHEALON_ALIAS.get(full)
        if name is None:
            for n in known:
                parts = n.split()
                if parts and parts[0] == last and first and first in n:
                    name = n
                    break
            else:
                for n in known:
                    if last and n.startswith(last):
                        name = n
                        break
        days = [FORM_DAY[d.strip()] for d in (r[4], r[5], r[6])
                if d and d.strip() in FORM_DAY]
        seen, ordered = set(), []
        for d in days:
            if d not in seen:
                seen.add(d)
                ordered.append(d)
        rec = {"form_name": full, "preferred_free_days": ordered,
               "role": (r[9] or "").strip(), "scope_change": (r[7] or "").strip(),
               "notes": (r[14] or "").strip()}
        if name is None:
            unknown.append(rec)
            continue
        # Un même prof a parfois rempli deux fois (nom inversé) : on fusionne.
        if name in out:
            for d in ordered:
                if d not in out[name]["preferred_free_days"]:
                    out[name]["preferred_free_days"].append(d)
            out[name]["role"] = out[name]["role"] or rec["role"]
        else:
            out[name] = rec
    return out, unknown


def grade_of(class_code: str) -> str:
    return class_code.split("-")[0].strip()


# ---------------------------------------------------------------- directeur
def read_director() -> list[dict]:
    """[{class, subject(nom שחף), teacher(nom שחף|None), hours}]"""
    recon: dict[str, str] = {}
    with open(DATA / "reconciliation_profs.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            d, s = row["nom_directeur"].strip(), row["nom_shahaf"].strip()
            recon[d] = s if s and s != "-" else d

    ws = openpyxl.load_workbook(XLSX, data_only=True)[SHEET]
    rows = list(ws.iter_rows(values_only=True))
    subj_at = {i: str(v).strip() for i, v in enumerate(rows[2]) if v and str(v).strip()}

    blocks: dict[str, list] = defaultdict(list)
    cur = None
    for r in rows[4:27]:
        c0 = str(r[0]).strip() if r[0] else ""
        if c0 and 'סה"כ' not in c0:
            cur = c0
        if cur:
            blocks[cur].append(r)

    out = []
    for raw_cls, rs in blocks.items():
        c = raw_cls.replace('- חנ"מ', "").replace(" ", "")
        cls = f"{c[0]}-{c[1:]}"
        for col, dsubj in subj_at.items():
            subj = DIR2SHAHAF.get(dsubj, dsubj)
            for r in rs:
                nm = str(r[col]).strip() if r[col] else ""
                hh = r[col + 1] if col + 1 < len(r) else None
                if not isinstance(hh, (int, float)) or hh <= 0:
                    continue
                if nm in ("·", ""):
                    nm = "לא משובץ"
                if "אמירים" in nm:
                    # La cellule porte « אמירים? » à la place d'un nom : c'est
                    # le programme d'excellence אמירים, poste non encore pourvu.
                    # On en fait une matière à part entière pour pouvoir la
                    # placer en fin de journée (Yossef 07/08).
                    subj, nm = "אמירים", "לא משובץ"
                out.append({"class": cls, "subject": subj,
                            "teacher": recon.get(nm, nm), "hours": int(round(hh))})
    return out


# -------------------------------------------------------------------- שחף
def read_shahaf():
    """Retourne (cours, cours olim reportés, heures de responsabilité par prof).

    Les heures de responsabilité (שהייה, פרטני, ישיבות, השתלמות…) ne sont pas
    des cours et ne sont donc pas placées dans la grille — mais elles disent
    combien de jours le prof est réellement présent. אלמו רפאל, chef du
    collège, n'a que 8h de cours mais 37h de responsabilités : le limiter à
    2 jours au motif de son petit service frontal serait absurde, et Yossef
    veut au contraire pouvoir s'appuyer sur ces profs-là pour boucher les
    trous (message du 07/08).
    """
    rikuz = json.loads((DATA / "rikuz_shaot_parsed.json").read_text(encoding="utf-8"))
    entries, postponed = [], []
    responsibility: dict[str, int] = defaultdict(int)
    for tname, t in rikuz.items():
        for l in t["lines"]:
            subj = l["subject"].strip()
            classes = [c.strip() for c in l["classes"] if c.strip()]
            if subj in NON_FRONTAL_SUBJECTS:
                responsibility[tname] += int(round(l["hours"]))
                continue
            if subj in EXCLUDE_SUBJECTS or not classes:
                continue
            rec = {"teacher": tname, "subject": subj,
                   "classes": frozenset(classes), "hours": int(round(l["hours"]))}
            (postponed if subj.endswith(" עולים") else entries).append(rec)
    return entries, postponed, dict(responsibility)


def drop_redundant(entries: list[dict]) -> tuple[list[dict], list[str]]:
    """Déduplique les lignes de שחף décrivant le MÊME cours.

    Deux cas, tous deux fréquents dans le rikuz :
      - lignes strictement identiques (prof, matière, classes) → une seule,
        heures = max ;
      - ligne « détail » dont le class-set est inclus dans un autre class-set
        du même prof pour la même matière : שמולביץ נדב של"ח [ט-3] n'est pas
        une heure de plus que son של"ח [ט-1,ט-3,ט-4], c'est la même heure vue
        classe par classe.
    """
    # 1. fusion des identiques
    fused: dict[tuple, dict] = {}
    for e in entries:
        k = (e["teacher"], e["subject"], e["classes"])
        if k in fused:
            fused[k]["hours"] = max(fused[k]["hours"], e["hours"])
        else:
            fused[k] = dict(e)
    merged = list(fused.values())

    # 2. absorption des sous-ensembles
    by_ts = defaultdict(list)
    for i, e in enumerate(merged):
        by_ts[(e["teacher"], e["subject"])].append(i)
    drop, report = set(), []
    for (t, s), idxs in by_ts.items():
        for i in idxs:
            for j in idxs:
                if i == j or j in drop:
                    continue
                a, b = merged[i]["classes"], merged[j]["classes"]
                if a < b:            # strictement inclus
                    drop.add(i)
                    report.append(f"{t} — {s} [{','.join(sorted(a))}] "
                                  f"absorbé par [{','.join(sorted(b))}]")
                    break
    n_fused = len(entries) - len(merged)
    if n_fused:
        report.insert(0, f"({n_fused} lignes strictement identiques fusionnées)")
    return [e for i, e in enumerate(merged) if i not in drop], report


def main():
    director = read_director()
    shahaf, postponed_olim, responsibility = read_shahaf()
    shahaf, redundant = drop_redundant(shahaf)

    capped_vie = []
    for e in shahaf:
        if e["subject"] in VIE_SCOLAIRE and e["hours"] > VIE_MAX_HOURS:
            capped_vie.append(f"{e['subject']} / {e['teacher']} "
                              f"[{','.join(sorted(e['classes']))}] "
                              f"{e['hours']}h → {VIE_MAX_HOURS}h")
            e["hours"] = VIE_MAX_HOURS

    dir_subjects = {e["subject"] for e in director}

    # --- Index שחף : (prof, matière, שכבה) -> classes de cette שכבה ---
    shahaf_sets: dict[tuple, set] = defaultdict(set)
    for e in shahaf:
        for g in {grade_of(c) for c in e["classes"]}:
            shahaf_sets[(e["teacher"], e["subject"], g)] |= {
                c for c in e["classes"] if grade_of(c) == g}

    # --- On retire de שחף tout ce que le directeur ré-écrit ---
    #     (matière académique חטיבה dont toutes les classes sont en חטיבה)
    kept_shahaf, replaced = [], 0
    for e in shahaf:
        grades = {grade_of(c) for c in e["classes"]}
        if e["subject"] in dir_subjects and grades <= set(HATIVA_GRADES):
            replaced += 1
            continue
        kept_shahaf.append(e)

    # --- Reconstruction חטיבה depuis le directeur ---
    # clé (שכבה, matière, prof, est-ce du חנ"מ) -> {classes directeur, heures}
    # Le drapeau חנ"מ est indispensable : הרב אברהמי enseigne תושב"ע 5h en ח-3
    # (dans la barrette de la שכבה) ET 2h en ח-2 (חנ"מ, groupe à part). Sans
    # ce drapeau les deux fusionnent et ח-2 se retrouve embarquée dans la
    # barrette avec l'enveloppe de 5h.
    by_gs: dict[tuple, dict] = defaultdict(lambda: defaultdict(
        lambda: {"classes": set(), "hours": 0}))
    for e in director:
        key = (grade_of(e["class"]), e["subject"], e["class"] in SPECIAL_ED)
        slot = by_gs[key][e["teacher"]]
        slot["classes"].add(e["class"])
        slot["hours"] = max(slot["hours"], e["hours"])

    rebuilt, holes_filled = [], []
    for (g, subj, is_sped), teachers in by_gs.items():
        for tname, info in teachers.items():
            dir_cls = info["classes"]
            if is_sped:
                # cours de חנ"מ : strictement la classe du directeur, jamais
                # complété par un lien de שכבה
                classes = set(dir_cls)
            else:
                cand = set(shahaf_sets.get((tname, subj, g), ()))
                cand -= {c for c in cand if c in SPECIAL_ED}
                classes = (cand | dir_cls) if cand else set(dir_cls)
            extra = classes - dir_cls
            if extra:
                holes_filled.append(
                    f"{subj} {g} / {tname} : +{','.join(sorted(extra))} (lien שחף)")
            rebuilt.append({"teacher": tname, "subject": subj,
                            "classes": frozenset(classes), "hours": info["hours"]})

    entries = kept_shahaf + rebuilt

    # --- Cours ajoutés à la main (absents des deux fichiers sources) ---
    for m in MANUAL_GROUPS:
        entries.append({"teacher": m["teacher"], "subject": m["subject"],
                        "classes": frozenset(m["classes"]), "hours": m["hours"]})
        print(f"  + ajout manuel : {m['teacher']} — {m['subject']} "
              f"[{','.join(m['classes'])}] {m['hours']}h", file=sys.stderr)

    # --- Profs partis → postes à pourvoir ---
    n_gone = 0
    for e in entries:
        if e["teacher"] in DEPARTED_TEACHERS:
            e["teacher"] = "לא משובץ"
            n_gone += 1
    if n_gone:
        print(f"\n=== {n_gone} cours libérés par des profs partis "
              f"({', '.join(sorted(DEPARTED_TEACHERS))}) ===", file=sys.stderr)

    # --- Placeholders pour לא משובץ ---
    n_ph = 0
    for e in entries:
        if e["teacher"] == "לא משובץ":
            n_ph += 1
            e["teacher"] = f"לא משובץ {n_ph}"
            e["placeholder"] = True
            if e["hours"] > 8:      # artefact d'agrégation שחף
                print(f"  ⚠ CAP {e['subject']} {sorted(e['classes'])} "
                      f"{e['hours']}h → 3h", file=sys.stderr)
                e["hours"] = 3

    # --- Cohortes (union-find : même matière + même שכבה + classes qui se recouvrent)
    def bucket(s):
        if s in MEGAMA_SUBJECTS:
            return "מגמות"
        return s[:-len(" עולים")].strip() if s.endswith(" עולים") else s

    parent = list(range(len(entries)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    by_key = defaultdict(list)
    for i, e in enumerate(entries):
        by_key[(bucket(e["subject"]),
                frozenset(grade_of(c) for c in e["classes"]))].append(i)
    for idxs in by_key.values():
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                i, j = idxs[a], idxs[b]
                if entries[i]["classes"] & entries[j]["classes"]:
                    ra, rb = find(i), find(j)
                    if ra != rb:
                        parent[rb] = ra

    comp = defaultdict(list)
    for i in range(len(entries)):
        comp[find(i)].append(i)

    # Un même prof ne peut pas tenir deux groupes SIMULTANÉS d'une même
    # barrette. On garde son groupe le plus large et on ABSORBE les autres.
    #
    # Absorber, et non pas les ressortir en cours séquentiels : la classe suit
    # déjà la matière pendant l'enveloppe de la barrette, donc en refaire un
    # cours à part lui ajoutait des heures qui n'existent pas. C'est ce qui
    # donnait 8h d'histoire à יא-2 (גז סטפני 4h en barrette + לוי יהונתן 4h
    # éjecté) là où תשפ"ו en comptait 6h — et poussait la classe à 54h, soit
    # 4h de plus que la semaine complète.
    absorbed, cohort_of, cohorts = [], {}, []
    dropped: set[int] = set()
    for idxs in comp.values():
        if len(idxs) < 2:
            continue
        by_teacher = defaultdict(list)
        for i in idxs:
            by_teacher[entries[i]["teacher"]].append(i)
        kept = []
        for t, tis in by_teacher.items():
            if len(tis) == 1:
                kept.extend(tis)
                continue
            tis.sort(key=lambda i: (-len(entries[i]["classes"]), -entries[i]["hours"]))
            kept.append(tis[0])
            for i in tis[1:]:
                dropped.add(i)
                absorbed.append(
                    f"{t} — {entries[i]['subject']} "
                    f"[{','.join(sorted(entries[i]['classes']))}] {entries[i]['hours']}h "
                    f"→ absorbé par son groupe "
                    f"[{','.join(sorted(entries[tis[0]]['classes']))}]")
        if len(kept) < 2:
            continue
        cls_union = sorted(set().union(*(entries[i]["classes"] for i in kept)))
        subs = sorted({entries[i]["subject"] for i in kept})
        cid = len(cohorts)
        cohorts.append({"label": f"הקבצה {'+'.join(subs)} [{','.join(cls_union)}]"[:190],
                        "classes": cls_union, "entries": kept,
                        "same_subject": len(subs) == 1})
        for i in kept:
            cohort_of[i] = cid

    # Les groupes absorbés disparaissent du modèle : on réindexe.
    keep_idx = [i for i in range(len(entries)) if i not in dropped]
    remap = {old: new for new, old in enumerate(keep_idx)}
    entries = [entries[i] for i in keep_idx]
    cohort_of = {remap[i]: c for i, c in cohort_of.items() if i in remap}
    for c in cohorts:
        c["entries"] = [remap[i] for i in c["entries"] if i in remap]

    # --- Référentiels ---
    all_classes = sorted({c for e in entries for c in e["classes"]})
    all_subjects = sorted({e["subject"] for e in entries})
    real_teachers = sorted({e["teacher"] for e in entries if not e.get("placeholder")})
    placeholders = sorted({e["teacher"] for e in entries if e.get("placeholder")})

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

    shealon, shealon_unknown = read_shealon(real_teachers)

    # Réunions : composition réelle depuis le rikuz. Un participant qui ne
    # revient pas est retiré ; ceux qui n'enseignent pas (חג'בי סמדר) sont
    # ajoutés à la liste des profs pour exister dans le modèle.
    meetings = []
    for m in read_meetings():
        parts = [p for p in m["participants"] if p not in DEPARTED_TEACHERS]
        if len(parts) >= 2:
            meetings.append({**m, "participants": parts})
    meeting_only = sorted({p for m in meetings for p in m["participants"]}
                          - set(real_teachers) - set(placeholders))
    real_teachers = sorted(set(real_teachers) | set(meeting_only))
    if meeting_only:
        print(f"\n=== {len(meeting_only)} participants de réunion sans cours : "
              f"{', '.join(meeting_only)} ===", file=sys.stderr)

    DAY = {"sunday": 0, "monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4}
    teachers_out, n_dispo = [], 0
    for name in real_teachers:
        blocks = []
        for p in dispo.get(name, []):
            d, per = DAY.get(p.get("day")), p.get("period")
            if d is not None and isinstance(per, int) and 1 <= per <= N_PERIODS:
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
        "placeholder": bool(e.get("placeholder")),
        "classes": sorted(e["classes"]), "hours": e["hours"],
        "cohort": cohort_of.get(i),
    } for i, e in enumerate(entries)]

    out = {
        "meta": {
            "school": 'אמי"ת בר אילן נתניה', "year": 'תשפ"ז (2026-2027)',
            "source": "שיבוץ מנהל (חטיבה) + שחף (מבנה הקבצות, חטיבה עליונה)",
            "week_days": 5, "periods_per_day": 11,
            "n_classes": len(all_classes), "n_subjects": len(all_subjects),
            "n_teachers": len(real_teachers), "n_placeholders": len(placeholders),
            "n_groups": len(groups_out), "n_cohorts": len(cohorts),
            "n_teachers_with_dispos": n_dispo,
            "n_shahaf_lines_replaced_by_director": replaced,
            "n_redundant_shahaf_lines_dropped": len(redundant),
            "n_vie_scolaire_capped": len(capped_vie),
            "n_postponed_olim": len(postponed_olim),
            "n_meetings": len(meetings),
            "n_meetings": len(meetings),
            "n_questionnaire_answers": len(shealon),
            "n_questionnaire_unknown": len(shealon_unknown),
        },
        "postponed_olim": [{"teacher": p["teacher"], "subject": p["subject"],
                            "classes": sorted(p["classes"]), "hours": p["hours"]}
                           for p in postponed_olim],
        "meetings": meetings,
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
    p('=== Consolidation תשפ"ז v2 (autorité directeur) ===')
    for k, v in out["meta"].items():
        p(f"  {k}: {v}")
    p(f"\n=== {len(capped_vie)} volumes de vie scolaire plafonnés "
      f"à {VIE_MAX_HOURS}h — À VALIDER ===")
    for line in capped_vie:
        p(f"  • {line}")
    p(f"\n=== {len(redundant)} lignes שחף redondantes absorbées ===")
    for line in redundant[:20]:
        p(f"  • {line}")
    p(f"\n=== {len(holes_filled)} trous du directeur comblés par les liens שחף ===")
    for line in holes_filled[:25]:
        p(f"  • {line}")
    if absorbed:
        p(f"\n=== {len(absorbed)} groupes absorbés (même prof deux fois dans un lien) "
          f"— À VALIDER ===")
        for line in absorbed:
            p(f"  • {line}")

    p("\n=== Charge hebdo par classe (max 55 = 5j × 11p) ===")
    load = defaultdict(int)
    for c in cohorts:
        env = max(entries[i]["hours"] for i in c["entries"])
        for cl in c["classes"]:
            load[cl] += env
    for i, e in enumerate(entries):
        if i not in cohort_of:
            for cl in e["classes"]:
                load[cl] += e["hours"]
    for cl in sorted(load, key=lambda x: (["ז", "ח", "ט", "י", "יא", "יב"].index(grade_of(x)), x)):
        flag = "  ⚠ SURCHARGE" if load[cl] > 52 else ""
        p(f"  {cl:<7} {load[cl]}h{flag}")


if __name__ == "__main__":
    main()
