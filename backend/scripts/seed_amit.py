"""Seed la DB avec les vraies données AMIT Bar Ilan Netanya extraites du PDF iscool.

Prérequis :
- Avoir lancé extract_amit_pdf.py qui produit amit_data.json
- DATABASE_URL pointant sur une DB (vide ou avec migrations à jour)

Crée :
- 1 école "AMIT Bar Ilan Netanya"
- 1 grille horaire complète : Dim-Jeu 8 créneaux + Ven 4 créneaux
- 6 שכבות (G7 à G12)
- 27 classes (réelles du PDF)
- 27 matières (dédupliquées) avec noms FR/HE
- 73 profs (avec heuristique de déduplication des noms collés)
- Groups (matière × classe) avec hours_per_week inféré du PDF (capé à 6h)
- Qualifications profs (qui enseigne quoi)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import time
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")

from sqlalchemy.orm import sessionmaker

from app.db.base import engine
import app.models  # noqa: F401
from app.models import (
    Class,
    Grade,
    Group,
    GroupingPolicy,
    GroupType,
    Room,
    School,
    Subject,
    Teacher,
    TimeSlot,
)


DATA_PATH = Path(__file__).parent / "amit_data.json"


# Codes matière → métadonnées (noms FR/HE/couleur/type salle)
SUBJECT_META = {
    "TEFILA":      ("ביאורי תפילה",  "Prière commentée",       "#9333ea", True,  None),
    "TANACH":      ('תנ"ך',           "Bible",                   "#7c3aed", True,  None),
    "TANACH_M":    ('תנ"ך מצויינים',  "Bible excellence",        "#5b21b6", True,  None),
    "TORAH_BAAL":  ("תורה שבעל פה",   "Torah orale",             "#a78bfa", True,  None),
    "TALMUD":      ("תלמוד",          "Talmud",                  "#8b5cf6", True,  None),
    "TALMUD_M":    ("תלמוד מצויינים", "Talmud excellence",       "#6d28d9", True,  None),
    "MACHSHEVET":  ("מחשבת ישראל",    "Pensée juive",            "#c084fc", True,  None),
    "MATH":        ("מתמטיקה",        "Mathématiques",           "#3b82f6", False, None),
    "ENGLISH":     ("אנגלית",         "Anglais",                 "#06b6d4", False, None),
    "SCIENCES":    ("מדעים",          "Sciences",                "#10b981", False, "lab"),
    "SCIENCES_M":  ("מדעים מצויינים", "Sciences excellence",     "#059669", False, "lab"),
    "HEVANA":      ("הבנה והבעה",      "Compréhension",           "#f59e0b", False, None),
    "HABAA_M":     ("הבעה מצויינים",   "Expression excellence",   "#d97706", False, None),
    "HEBREW":      ("עברית",          "Hébreu",                  "#eab308", False, None),
    "LASHON":      ("לשון",           "Langue",                  "#ca8a04", False, None),
    "SIFRUT":      ("ספרות",          "Littérature",             "#a16207", False, None),
    "TOLDOT":      ("תולדות עם",      "Histoire du peuple",      "#dc2626", False, None),
    "HISTORY":     ("היסטוריה",       "Histoire",                "#b91c1c", False, None),
    "EZRAHUT":     ("אזרחות",         "Civisme",                 "#991b1b", False, None),
    "GYM":         ("חינוך גופני",    "Sport",                   "#22c55e", False, "gym"),
    "FRENCH":      ("צרפתית",         "Français",                "#0ea5e9", False, None),
    "ELEC":        ("אלקטרוניקה",     "Électronique",            "#64748b", False, "lab"),
    "CS":          ("מדעי המחשב",     "Informatique",            "#475569", False, "lab"),
    "PHYSICS":     ("פיסיקה",         "Physique",                "#334155", False, "lab"),
    "TIKSHORET":   ("מערכות תקשורת",  "Comm. systems",           "#1e293b", False, "lab"),
    "BUSINESS":    ("ניהול עסקי",     "Gestion",                 "#0f172a", False, None),
    "ENVIRONMENT": ("לימודי הסביבה",  "Env. sciences",           "#16a34a", False, None),
    "KISHURIM":    ("כישורי חיים",    "Life skills",             "#f97316", False, None),
    "SHELACH":     ('של"ח',           "Field activity",          "#ea580c", False, None),
    "SHELAM":      ('של"ם',           "Special program",         "#c2410c", False, None),
    "EDUCATION":   ("חינוך",          "Heure de vie",            "#a3a3a3", False, None),
    "AMIRIM":      ("אמירים",         "Programme excellence",    "#facc15", False, None),
    "OFFLINE":     ("לא משובץ",       "Non placé",               "#9ca3af", False, None),
}


def dedupe_teachers(raw_teachers: list[str]) -> tuple[list[str], dict[str, str]]:
    """Heuristique : si "A B C D" et "A B C" existent tous deux, on garde "A B C" et on mappe.

    Retourne (liste_dédupliquée, mapping_original→canonical).
    """
    sorted_by_len = sorted(raw_teachers, key=len)
    canonical = []
    mapping = {}
    for name in sorted_by_len:
        # Voir si c'est un préfixe (mot à mot) d'un nom déjà canonicalisé... non, on garde le plus court.
        # En fait : si name est un préfixe word-wise d'un nom plus long, on garde name comme canonique.
        # On itère et on accepte un nom seulement si aucun préfixe word-wise plus court n'est déjà accepté.
        words = name.split()
        # Si on a déjà un canonical qui est un préfixe des words de "name", on l'absorbe
        absorbed = False
        for c in canonical:
            c_words = c.split()
            if len(c_words) < len(words) and words[: len(c_words)] == c_words:
                # name est plus long ET commence par c → c'est probablement une concaténation
                mapping[name] = c
                absorbed = True
                break
        if not absorbed:
            canonical.append(name)
            mapping[name] = name
    return canonical, mapping


def make_teacher_code(name: str, used: set[str]) -> str:
    """Génère un code court unique depuis un nom."""
    # Premières lettres de chaque mot
    parts = name.split()
    if len(parts) == 1:
        base = parts[0][:3]
    else:
        base = "".join(p[0] for p in parts[:3])
    code = base
    i = 1
    while code in used:
        i += 1
        code = f"{base}{i}"
    used.add(code)
    return code


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = Session()

    if db.query(School).filter_by(code="amit-netanya").first():
        print("AMIT déjà seedé. Supprime demo.db pour repartir à zéro.")
        return

    # 1. École
    school = School(code="amit-netanya", name="אמי\"ת בר אילן נתניה", default_language="he")
    db.add(school)
    db.flush()
    print(f"+ School #{school.id}")

    # 2. Grille horaire : Dim-Jeu (jours 0-4) + Ven (5) creneau 0-7 + Ven 0-3
    for day in range(5):  # Dim..Jeu
        # Créneau 0 (ביאורי תפילה) + 1-10
        for slot in range(11):
            start_h = 7 + slot
            db.add(TimeSlot(
                school_id=school.id, day_of_week=day, slot_index=slot,
                start_time=time(start_h % 24, 0), end_time=time(start_h % 24, 45),
                is_active=True, is_break=False, label=None,
            ))
    # Vendredi : 4 créneaux seulement
    for slot in range(4):
        start_h = 7 + slot
        db.add(TimeSlot(
            school_id=school.id, day_of_week=5, slot_index=slot,
            start_time=time(start_h, 0), end_time=time(start_h, 45),
            is_active=True, is_break=False, label=None,
        ))
    db.flush()
    print(f"+ TimeGrid : Dim-Jeu × 11 créneaux + Ven × 4 = 59 slots")

    # 3. Grades (שכבות)
    GRADE_INFO = [
        ("G7", "ז", "שכבה ז", 7),
        ("G8", "ח", "שכבה ח", 8),
        ("G9", "ט", "שכבה ט", 9),
        ("G10", "י", "שכבה י", 10),
        ("G11", "יא", "שכבה י\"א", 11),
        ("G12", "יב", "שכבה י\"ב", 12),
    ]
    grades = {}
    for code, _, name, order in GRADE_INFO:
        g = Grade(
            school_id=school.id, code=code, name=name, order=order,
            grouping_policy=GroupingPolicy.GROUP_CENTRIC,  # AMIT utilise des barrettes
        )
        db.add(g)
        db.flush()
        grades[code] = g
    print(f"+ {len(grades)} שכבות")

    # 4. Classes
    classes_obj = {}
    for c in data["classes"]:
        grade_code = c["grade"]
        if not grade_code:
            # אולפן, כיתת עולים — sans grade : on les crée avec un grade "spécial" G7 par défaut
            grade_code = "G7"
        gid = grades[grade_code].id
        # Code = label simplifié pour URL
        code = c["label"].replace(" ", "-").replace('"', "").replace("'", "")
        cls = Class(
            school_id=school.id, grade_id=gid,
            code=code, name=c["label"], student_count=25,
        )
        db.add(cls)
        db.flush()
        classes_obj[c["label"]] = cls
    print(f"+ {len(classes_obj)} classes")

    # 5. Matières
    subjects_obj = {}
    for code in data["subjects"]:
        if code not in SUBJECT_META:
            continue
        name_he, name_fr, color, religious, room_type = SUBJECT_META[code]
        s = Subject(
            school_id=school.id, code=code,
            name_fr=name_fr, name_he=name_he, abbreviation=code[:6],
            color_hex=color, required_room_type=room_type,
            is_religious=religious, is_active=True,
        )
        db.add(s)
        db.flush()
        subjects_obj[code] = s
    print(f"+ {len(subjects_obj)} matières")

    # 6. Profs (déduplication)
    raw_teachers = data["teachers"]
    canonical, mapping = dedupe_teachers(raw_teachers)
    print(f"+ {len(raw_teachers)} → {len(canonical)} profs après dédup")

    teachers_obj = {}
    used_codes: set[str] = set()
    for name in canonical:
        code = make_teacher_code(name, used_codes)
        parts = name.split()
        first_name = parts[0] if parts else name
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        t = Teacher(
            school_id=school.id, code=code,
            first_name=first_name, last_name=last_name,
            email=None, phone=None,
            languages=["he", "fr"], max_hours_per_week=24, max_hours_per_day=8,
            is_active=True,
        )
        db.add(t)
        db.flush()
        teachers_obj[name] = t

    # 7. Qualifications (qui enseigne quoi) — depuis subject_to_teachers
    for subj_code, teacher_names in data["subject_to_teachers"].items():
        if subj_code not in subjects_obj:
            continue
        subj = subjects_obj[subj_code]
        seen_in_subj: set[str] = set()
        for tname in teacher_names:
            canonical_name = mapping.get(tname, tname)
            if canonical_name in seen_in_subj:
                continue
            seen_in_subj.add(canonical_name)
            if canonical_name in teachers_obj:
                t = teachers_obj[canonical_name]
                if subj not in t.qualified_subjects:
                    t.qualified_subjects.append(subj)
    db.flush()
    qualif_count = sum(len(t.qualified_subjects) for t in teachers_obj.values())
    print(f"+ {qualif_count} qualifications profs↔matières")

    # 8. Salles (génériques pour l'instant : 1 par classe + 2 labs + 1 gym)
    rooms_obj = {}
    for i in range(20):
        r = Room(school_id=school.id, code=f"R{i+1:02d}",
                  name=f"חדר {i+1}", capacity=30, is_active=True)
        db.add(r)
        rooms_obj[f"R{i+1:02d}"] = r
    for i in range(3):
        r = Room(school_id=school.id, code=f"LAB{i+1}",
                  name=f"מעבדה {i+1}", capacity=24, room_type="lab", is_active=True)
        db.add(r)
    db.add(Room(school_id=school.id, code="GYM", name="אולם ספורט",
                 capacity=60, room_type="gym", is_active=True))
    db.flush()
    print(f"+ 24 salles (20 standard + 3 labs + 1 gym)")

    # 9. Groups : pour chaque (classe, matière) où le PDF avait du contenu, créer un Group.
    # hours_per_week = min(6, count) avec heuristique (count brut / 5 jours pour estimer)
    n_groups = 0
    for c in data["classes"]:
        cls = classes_obj[c["label"]]
        for subj_code, count in c["subjects"].items():
            if subj_code not in subjects_obj or subj_code == "OFFLINE":
                continue
            subj = subjects_obj[subj_code]
            # Estimation : nombre d'occurrences / 5 jours, capé à 6h
            hours = max(1, min(6, count // 5)) if count >= 5 else max(1, count // 3 or 1)

            # Profs : ceux qui enseignent cette matière à cette classe
            teacher_names_raw = c["teachers_per_subject"].get(subj_code, [])
            tids = []
            for tn in teacher_names_raw:
                canon = mapping.get(tn, tn)
                if canon in teachers_obj:
                    tid = teachers_obj[canon].id
                    if tid not in tids:
                        tids.append(tid)

            g = Group(
                school_id=school.id, grade_id=cls.grade_id, subject_id=subj.id,
                label=f"{subj_code} {c['label']}", hours_per_week=hours,
                group_type=GroupType.WHOLE_CLASS, student_count=cls.student_count,
            )
            g.source_classes.append(cls)
            for tid in tids:
                t = next((t for t in teachers_obj.values() if t.id == tid), None)
                if t:
                    g.teachers.append(t)
            db.add(g)
            n_groups += 1
    db.flush()
    print(f"+ {n_groups} groups")

    db.commit()
    print(f"\n✅ Seed AMIT terminé. school_id = {school.id}")
    print(f"   {len(classes_obj)} classes / {len(subjects_obj)} matières / {len(canonical)} profs / {n_groups} groups")


if __name__ == "__main__":
    main()
