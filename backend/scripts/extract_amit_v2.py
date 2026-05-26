"""Extracteur AMIT v2 — table-aware avec détection des barrettes.

Utilise PyMuPDF (fitz) pour extraire les cellules tabulaires du PDF iscool.
Pour chaque cellule (classe, créneau, jour) on parse les matières + profs.

Une cellule avec 2+ matières DIFFÉRENTES = barrette (élèves choisissent un track).
Si le même set de matières apparaît sur plusieurs cellules du même grade,
on crée une ParallelCohort partagée.

Produit : amit_data_v2.json avec en plus la liste des barrettes détectées.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import fitz


PDF_PATH = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\USER\AppData\Local\Temp\amit.pdf"
OUT_JSON = Path(__file__).parent / "amit_data_v2.json"


SUBJECT_PATTERNS = {
    "TEFILA": ["ביאורי תפי"],
    "TANACH_M": ['תנ"ך מצויי'],  # match avant "תנ"ך"
    "TANACH": ['תנ"ך'],
    "TALMUD_M": ["תלמוד מצוי"],
    "TALMUD": ["תלמוד"],
    "TORAH_BAAL": ["תורה שבעל"],
    "MACHSHEVET": ["מחשבת ישרא"],
    "SCIENCES_M": ["מדעים מצוי"],
    "SCIENCES": ["מדעים"],
    "MATH": ["מתמטיקה"],
    "ENGLISH": ["אנגלית"],
    "HEVANA": ["הבנה והבעה"],
    "HABAA_M": ["הבעה מצויי"],
    "HEBREW": ["עברית"],
    "LASHON": ["לשון"],
    "SIFRUT": ["ספרות"],
    "TOLDOT": ["תולדות עם"],
    "HISTORY": ["היסטוריה"],
    "EZRAHUT": ["אזרחות"],
    "GYM": ["חינוך גופנ"],
    "FRENCH": ["צרפתית"],
    "ELEC": ["אלקטרוניקה"],
    "CS": ["מדעי המחשב"],
    "PHYSICS": ["פיסיקה"],
    "TIKSHORET": ["מערכות תקשורת"],
    "BUSINESS": ["ניהול עסקי"],
    "ENVIRONMENT": ["לימודי הסביבה"],
    "KISHURIM": ["כישורי חיי"],
    "SHELACH": ['של"ח'],
    "SHELAM": ['של"ם'],
    "AMIRIM": ["אמירים"],
    "EDUCATION": ["חינוך"],
    "OFFLINE": ["לא משובץ"],
}


# Reconstitue un nom de prof depuis ligne RTL inversée
HEBREW_NAME_RE = re.compile(r"[א-ת]+(?:\s+[א-ת]+){1,3}")


def reverse_rtl(text: str) -> str:
    """Inverse caractère par caractère (PyMuPDF rend RTL inversé)."""
    if not text:
        return ""
    return "\n".join(line[::-1] for line in text.split("\n"))


def parse_cell(cell_text: str) -> dict:
    """Parse une cellule : retourne {subjects: [code, ...], teachers_per_subject: {...}}.

    Une cellule peut contenir plusieurs blocs matière+profs séparés par un caractère
    spécial (​ dans PyMuPDF) ou par un saut de ligne avant un nouveau nom de matière.
    """
    if not cell_text:
        return {"subjects": [], "teachers_per_subject": {}}
    text = reverse_rtl(cell_text)
    # Strip zero-width chars
    text = text.replace("​", "")
    lines = [ln.strip().rstrip(",") for ln in text.split("\n") if ln.strip()]

    # On itère ligne par ligne. Chaque ligne qui matche un pattern matière commence
    # un nouveau bloc. Les lignes suivantes (jusqu'à la prochaine matière) sont les profs.
    subjects: list[str] = []
    teachers_per_subject: dict[str, list[str]] = defaultdict(list)
    current = None
    current_text = ""

    def flush():
        if current and current_text:
            # Parser profs : split par virgule
            chunks = [c.strip() for c in current_text.split(",") if c.strip()]
            for chunk in chunks:
                if HEBREW_NAME_RE.fullmatch(chunk):
                    if chunk not in teachers_per_subject[current]:
                        teachers_per_subject[current].append(chunk)

    for line in lines:
        # Strip "(פ)" annotation
        line_clean = re.sub(r"\([^)]*\)", "", line).strip()
        subj = None
        for code, variants in SUBJECT_PATTERNS.items():
            if any(v in line_clean for v in variants):
                subj = code
                break

        if subj:
            flush()
            current = subj
            current_text = ""
            if subj not in subjects:
                subjects.append(subj)
        elif current:
            current_text += " " + line

    flush()

    return {
        "subjects": subjects,
        "teachers_per_subject": dict(teachers_per_subject),
    }


def extract_class_label(text: str, page_idx: int) -> str | None:
    """Détecte le label de classe au début de la page (ou avant le tableau)."""
    # Pattern "Nמערכת שעות לכיתה X" peut apparaître en RTL inversé : "X הכיתל תועש תכרעמ N"
    # ou en LTR si la page est extraite différemment
    # On cherche les deux
    rev = reverse_rtl(text)
    for src in (text, rev):
        m = re.search(r"(\d?)\s*מערכת שעות לכיתה\s*([^\n]+)", src)
        if m:
            num = m.group(1).strip()
            label = m.group(2).strip()
            return f"{label}-{num}" if num else label
    return None


def main():
    doc = fitz.open(PDF_PATH)
    print(f"Pages: {doc.page_count}", file=sys.stderr)

    # Pour chaque classe : dict des cellules détectées
    # classes[label] = [{day, slot, subjects, teachers_per_subject}, ...]
    classes_cells: dict[str, list[dict]] = defaultdict(list)
    current_class = None

    for pidx, page in enumerate(doc):
        # Detect class label
        page_text = page.get_text()
        label = extract_class_label(page_text, pidx)
        if label:
            current_class = label
            print(f"[Page {pidx+1}] classe : {label}", file=sys.stderr)

        if not current_class:
            continue

        tables = page.find_tables()
        for tab in tables.tables:
            if tab.col_count < 6:
                continue  # pas la table emploi du temps
            rows = tab.extract()
            if not rows:
                continue
            # Trouver la ligne d'en-tête : doit contenir "שעה" (peut être RTL)
            header_row_idx = None
            for r, row in enumerate(rows):
                header_text = " ".join(c or "" for c in row)
                if "שעה" in header_text or "העש" in header_text:
                    header_row_idx = r
                    break
            if header_row_idx is None:
                continue

            # La colonne שעה est la dernière (col_count - 1) en LTR ou la 1ère en RTL.
            # Détection : trouver la colonne avec "שעה" / "העש"
            header = rows[header_row_idx]
            slot_col = None
            for c, val in enumerate(header):
                if val and ("שעה" in val or "העש" in val):
                    slot_col = c
                    break
            if slot_col is None:
                continue

            # Jours : 6 colonnes maximum, ordre RTL = Dim,Lun,Mar,Mer,Jeu,Ven de droite à gauche
            # Si slot_col = 6 (dernière), alors col 5 = Dim (יום א), col 4 = Lun, ... col 0 = Ven
            # Si slot_col = 0 (première), alors col 1 = Dim, ... col 6 = Ven
            day_cols = []  # ordered list of (col_idx, day_num 0..5)
            if slot_col == tab.col_count - 1:
                # RTL : col 5=Dim, 4=Lun, 3=Mar, 2=Mer, 1=Jeu, 0=Ven
                for c in range(tab.col_count - 1):
                    day_num = (tab.col_count - 2) - c  # col 5 -> 0 (Dim), col 0 -> 5 (Ven)
                    day_cols.append((c, day_num))
            else:
                # LTR : col 0=שעה, col 1=Dim, ..., col 6=Ven
                for c in range(1, tab.col_count):
                    day_cols.append((c, c - 1))

            for r in range(header_row_idx + 1, tab.row_count):
                row = rows[r]
                # Slot index
                slot_raw = row[slot_col]
                if slot_raw is None:
                    continue
                slot_match = re.search(r"\d+", slot_raw)
                if not slot_match:
                    continue
                slot_idx = int(slot_match.group(0))
                for c, day_num in day_cols:
                    cell = row[c] if c < len(row) else None
                    parsed = parse_cell(cell)
                    if parsed["subjects"]:
                        classes_cells[current_class].append({
                            "day": day_num,
                            "slot": slot_idx,
                            "subjects": parsed["subjects"],
                            "teachers_per_subject": parsed["teachers_per_subject"],
                        })

    # Calculer : agrégations par classe
    classes_summary = []
    all_subjects: set[str] = set()
    all_teachers: set[str] = set()
    subject_to_teachers: dict[str, set[str]] = defaultdict(set)

    # Barrettes détectées : pour chaque classe, liste des sets de matières trouvés en multi-cellule
    barrettes_per_class: dict[str, set[frozenset[str]]] = defaultdict(set)

    for label, cells in classes_cells.items():
        subj_count: Counter = Counter()
        teachers_per_subj: dict[str, set[str]] = defaultdict(set)
        for cell in cells:
            for s in cell["subjects"]:
                subj_count[s] += 1
                all_subjects.add(s)
            # Barrette ? plusieurs matières dans cette cellule
            if len(cell["subjects"]) >= 2:
                bs = frozenset(cell["subjects"])
                barrettes_per_class[label].add(bs)
            for s, ts in cell["teachers_per_subject"].items():
                for t in ts:
                    teachers_per_subj[s].add(t)
                    all_teachers.add(t)
                    subject_to_teachers[s].add(t)
        classes_summary.append({
            "label": label,
            "subjects": dict(subj_count),
            "teachers_per_subject": {k: sorted(v) for k, v in teachers_per_subj.items()},
            "barrettes": [sorted(b) for b in barrettes_per_class[label]],
            "n_cells": len(cells),
        })

    # Inférer la שכבה
    GRADE_MAP = {"ז": "G7", "ח": "G8", "ט": "G9", "י": "G10", "יא": "G11", "יב": "G12"}
    def infer_grade(label: str):
        clean = label.replace("שילוב ", "").strip()
        for k in ["יא", "יב", "ז", "ח", "ט", "י"]:
            if clean.startswith(k):
                return GRADE_MAP[k]
        return None
    for c in classes_summary:
        c["grade"] = infer_grade(c["label"])

    # Barrettes au niveau שכבה : pour chaque grade, set de barrettes uniques
    grade_barrettes: dict[str, list[list[str]]] = defaultdict(list)
    for c in classes_summary:
        if not c["grade"]:
            continue
        for bset in c["barrettes"]:
            if bset not in grade_barrettes[c["grade"]]:
                grade_barrettes[c["grade"]].append(bset)

    out = {
        "classes": classes_summary,
        "subjects": sorted(all_subjects),
        "teachers": sorted(all_teachers),
        "subject_to_teachers": {s: sorted(ts) for s, ts in subject_to_teachers.items()},
        "grade_barrettes": grade_barrettes,
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n=== Résumé v2 ===", file=sys.stderr)
    print(f"  {len(classes_summary)} classes", file=sys.stderr)
    print(f"  {len(all_subjects)} matières", file=sys.stderr)
    print(f"  {len(all_teachers)} profs", file=sys.stderr)
    print(f"  Barrettes par שכבה :", file=sys.stderr)
    for g, bs in grade_barrettes.items():
        print(f"    {g} : {len(bs)} patterns uniques", file=sys.stderr)
        for b in bs:
            print(f"      • {' + '.join(b)}", file=sys.stderr)


if __name__ == "__main__":
    main()
