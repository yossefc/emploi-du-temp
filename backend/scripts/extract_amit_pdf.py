"""Extrait les données de l'export iscool AMIT Bar Ilan Netanya.

Le PDF est généré par iscool.co.il (envoyé par mail). Format :
- Chaque classe a un bloc "Nמערכת שעות לכיתה X" où N = numéro de la classe
- Sous chaque classe, table créneaux × jours
- Chaque cellule peut contenir 1 ou plusieurs matières (barrettes) avec leurs profs

Produit :
- backend/scripts/amit_data.json : structure JSON utilisable par seed_amit.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pypdf


PDF_PATH = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\USER\AppData\Local\Temp\amit.pdf"
OUT_JSON = Path(__file__).parent / "amit_data.json"


def extract_text(pdf_path: str) -> str:
    reader = pypdf.PdfReader(pdf_path)
    return "\n".join(page.extract_text() for page in reader.pages)


def split_class_blocks(text: str) -> list[tuple[str, str]]:
    """Découpe le texte en blocs (class_label, body)."""
    # Pattern : optional digit prefix + "מערכת שעות לכיתה" + label jusqu'à fin de ligne
    pattern = re.compile(r"(\d?)מערכת שעות לכיתה\s*([^\n]+?)(?=\n)")
    matches = list(pattern.finditer(text))
    blocks = []
    for i, m in enumerate(matches):
        num = m.group(1).strip()
        label = m.group(2).strip()
        full = f"{label}-{num}" if num else label
        # Body = jusqu'au prochain match (ou fin du texte)
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end() : body_end]
        blocks.append((full, body))
    return blocks


# Matières (codes simplifiés pour l'API).
# Détectées dans le PDF. On dédupe les variantes (ex: "תנ"ך - בי"" → "תנ"ך").
SUBJECT_PATTERNS = {
    # ORDRE IMPORTANT : les variantes "מצויי" (excellence) doivent être listées AVANT
    # les versions standard (sinon "תנ\"ך" matche "תנ\"ך מצויי" en premier).
    "TEFILA": ["ביאורי תפי", "ביאורי תפילה"],
    "TANACH_M": ['תנ"ך מצויי', 'תנ"ך מצויינים'],
    "TANACH": ['תנ"ך'],
    "TALMUD_M": ["תלמוד מצוי"],
    "TALMUD": ["תלמוד"],
    "TORAH_BAAL": ["תורה שבעל"],
    "MACHSHEVET": ["מחשבת ישרא", "מחשבת ישראל"],
    "MATH": ["מתמטיקה"],
    "ENGLISH": ["אנגלית"],
    "SCIENCES_M": ["מדעים מצוי"],
    "SCIENCES": ["מדעים"],
    "HEVANA": ["הבנה והבעה"],
    "HABAA_M": ["הבעה מצויי"],
    "HEBREW": ["עברית"],
    "LASHON": ["לשון"],
    "SIFRUT": ["ספרות"],
    "TOLDOT": ["תולדות עם"],
    "HISTORY": ["היסטוריה"],
    "EZRAHUT": ["אזרחות"],
    "GYM": ["חינוך גופנ", "חינוך גופני"],
    "FRENCH": ["צרפתית"],
    "ELEC": ["אלקטרוניקה"],
    "CS": ["מדעי המחשב"],
    "PHYSICS": ["פיסיקה"],
    "TIKSHORET": ["מערכות תקשורת"],
    "BUSINESS": ["ניהול עסקי"],
    "ENVIRONMENT": ["לימודי הסביבה"],
    "KISHURIM": ["כישורי חיי", "כישורי חיים"],
    "SHELACH": ['של"ח'],
    "SHELAM": ['של"ם'],
    "EDUCATION": ["חינוך"],
    "AMIRIM": ["אמירים"],
    "OFFLINE": ["לא משובץ"],
}


def find_subject(line: str) -> str | None:
    for code, variants in SUBJECT_PATTERNS.items():
        for v in variants:
            if v in line:
                return code
    return None


# Regex pour détecter un nom de prof (2-4 mots hébreux séparés par espaces, optionnellement précédés/suivis de virgule)
# Un nom typique : "דיין ישראל", "ספר מוריס יוני", "כהן זרדי יוסף אליהו"
HEBREW_NAME_RE = re.compile(r"[א-ת]+(?:\s+[א-ת]+){1,3}")


def parse_class_body(body: str) -> dict:
    """Parse le contenu d'une classe : retourne {subjects: {subject_code: hours_count}, teachers: [...]}.

    Logique : on découpe par lignes, et pour chaque ligne où on détecte une matière,
    on essaye d'extraire le prof sur les lignes suivantes (jusqu'à la prochaine matière
    ou un séparateur).
    """
    lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
    subjects_count: Counter = Counter()
    teachers_per_subject: dict[str, set[str]] = defaultdict(set)
    all_teachers: set[str] = set()

    i = 0
    while i < len(lines):
        line = lines[i]
        subj = find_subject(line)
        if subj:
            subjects_count[subj] += 1
            # Chercher les profs : lignes suivantes jusqu'à la prochaine matière
            j = i + 1
            collected_text = ""
            while j < len(lines) and not find_subject(lines[j]) and j - i < 6:
                # éviter de ramasser des numéros de créneau
                if not re.match(r"^\d+$", lines[j]):
                    collected_text += " " + lines[j]
                j += 1
            # Extraire les noms : pattern noms séparés par virgules
            # On découpe d'abord par virgule, puis on trim
            for chunk in re.split(r"[,،]", collected_text):
                chunk = chunk.strip()
                # Garder seulement les chunks qui ressemblent à un nom (au moins 2 mots hébreux)
                if HEBREW_NAME_RE.fullmatch(chunk):
                    teachers_per_subject[subj].add(chunk)
                    all_teachers.add(chunk)
            i = j
        else:
            i += 1

    return {
        "subjects_count": dict(subjects_count),
        "teachers_per_subject": {k: sorted(v) for k, v in teachers_per_subject.items()},
        "all_teachers": sorted(all_teachers),
    }


def main():
    print(f"Reading {PDF_PATH}...", file=sys.stderr)
    text = extract_text(PDF_PATH)
    blocks = split_class_blocks(text)
    print(f"Found {len(blocks)} class blocks", file=sys.stderr)

    classes_data = []
    all_subjects: set[str] = set()
    all_teachers: set[str] = set()
    # Pour chaque matière : ensemble des profs qui l'enseignent (toutes classes confondues)
    subject_to_teachers: dict[str, set[str]] = defaultdict(set)

    for label, body in blocks:
        parsed = parse_class_body(body)
        classes_data.append({
            "label": label,
            "subjects": parsed["subjects_count"],
            "teachers_per_subject": parsed["teachers_per_subject"],
        })
        all_subjects.update(parsed["subjects_count"].keys())
        all_teachers.update(parsed["all_teachers"])
        for s, ts in parsed["teachers_per_subject"].items():
            subject_to_teachers[s].update(ts)

    # Inférer la שכבה (grade) depuis le label
    GRADE_MAP = {"ז": "G7", "ח": "G8", "ט": "G9", "י": "G10", "יא": "G11", "יב": "G12"}
    def infer_grade(label: str) -> str | None:
        # Strip "שילוב " prefix
        clean = label.replace("שילוב ", "").strip()
        # First char(s)
        for k in ["יא", "יב", "ז", "ח", "ט", "י"]:
            if clean.startswith(k):
                return GRADE_MAP[k]
        return None  # אולפן, כיתת עולים — pas de grade

    for c in classes_data:
        c["grade"] = infer_grade(c["label"])

    out = {
        "classes": classes_data,
        "subjects": sorted(all_subjects),
        "teachers": sorted(all_teachers),
        "subject_to_teachers": {s: sorted(ts) for s, ts in subject_to_teachers.items()},
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== Résumé ===", file=sys.stderr)
    print(f"  {len(classes_data)} classes", file=sys.stderr)
    print(f"  {len(all_subjects)} matières uniques", file=sys.stderr)
    print(f"  {len(all_teachers)} profs uniques", file=sys.stderr)
    print(f"  Sortie : {OUT_JSON}", file=sys.stderr)


if __name__ == "__main__":
    main()
