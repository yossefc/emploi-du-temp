# Guide des Données de Test - École Israélienne

## 📋 Vue d'Ensemble

Ce système de données de test crée un environnement complet et réaliste pour une école israélienne avec :
- **Support bilingue** français/hébreu
- **Système scolaire israélien** (collège/lycée grades 7-12)
- **Semaine israélienne** (dimanche-jeudi + vendredi court)
- **Matières spécialisées** (religieuses, sciences, arts)
- **Contraintes culturelles** (séparation des sexes, Shabbat)

## 🎯 Données Créées

### 👥 Utilisateurs (4)
| Username | Email | Rôle | Langue | Nom |
|----------|-------|------|--------|-----|
| `admin` | admin@school.edu.il | ADMIN | he | מנהל המערכת |
| `principal` | principal@school.edu.il | ADMIN | fr | Sarah Cohen |
| `coordinator` | coordinator@school.edu.il | TEACHER | he | דוד לוי |
| `secretary` | secretary@school.edu.il | VIEWER | fr | Marie Dubois |

**Mot de passe par défaut**: `password123`

### 👨‍🏫 Enseignants (11)
| Code | Nom | Spécialités | Langue |
|------|-----|-------------|--------|
| T001 | רחל כהן | Hébreu, Histoire juive | he |
| T002 | David Levy | Mathématiques | he |
| T003 | Sarah Martin | Français | fr |
| T004 | יוסף רוזנברג | Physique, Math | he |
| T005 | Marie Dubois | Anglais | fr |
| T006 | אברהם גולדשטיין | Torah, Talmud | he |
| T007 | מרים שפירא | Chimie, Biologie | he |
| T008 | Pierre Moreau | Géographie, Histoire | fr |
| T009 | אסתר בן-דוד | Arts, Musique | he |
| T010 | משה כץ | Éducation physique | he |
| T011 | נטע אבן | Informatique | he |

### 📚 Matières (15)
#### Langues
- **HEB001**: עברית / Hébreu
- **ENG001**: אנגלית / Anglais  
- **FRE001**: צרפתית / Français

#### Sciences & Math
- **MATH001**: מתמטיקה / Mathématiques
- **PHYS001**: פיזיקה / Physique (laboratoire)
- **CHEM001**: כימיה / Chimie (laboratoire)
- **BIO001**: ביולוגיה / Biologie (laboratoire)
- **CS001**: מדעי המחשב / Informatique

#### Sciences Humaines
- **HIST001**: תולדות עם ישראל / Histoire du peuple juif
- **GEO001**: גיאוגרפיה / Géographie

#### Matières Religieuses
- **TORA001**: תורה / Torah (séparation des sexes)
- **TALM001**: תלמוד / Talmud (séparation des sexes)

#### Arts & Sports
- **ART001**: אמנות / Arts plastiques
- **MUS001**: מוזיקה / Musique
- **PE001**: חינוך גופני / Éducation physique (séparation des sexes)

### 🎓 Classes (12)
#### Collège
- **7A/7B**: כיתה ז1/ז2 (Grade 7, 28/26 élèves)
- **8A/8B**: כיתה ח1/ח2 (Grade 8, 30/27 élèves)
- **9A/9B**: כיתה ט1/ט2 (Grade 9, 29/25 élèves)

#### Lycée
- **10A**: כיתה י1 (Grade 10 Avancé, 24 élèves)
- **10B**: כיתה י2 (Grade 10 Standard, 22 élèves)
- **11A**: כיתה יא1 (Grade 11 Avancé, 20 élèves)
- **11B**: כיתה יא2 (Grade 11 Standard, 18 élèves)
- **12A**: כיתה יב1 (Grade 12 Avancé, 19 élèves)
- **12B**: כיתה יב2 (Grade 12 Standard, 17 élèves)

### 🏢 Salles (16)
#### Salles Standard
- **101-104**: אולם 101-104 (35 places)
- **201-204**: אולם 201-204 (30 places)

#### Laboratoires
- **LAB_PHYS**: מעבדת פיזיקה (20 places)
- **LAB_CHEM**: מעבדת כימיה (20 places)
- **LAB_BIO**: מעבדת ביולוגיה (20 places)
- **LAB_CS**: מעבדת מחשבים (25 places)

#### Salles Spécialisées
- **GYM**: אולם התעמלות (60 places)
- **ART**: חדר אמנות (25 places)
- **MUS**: חדר מוזיקה (30 places)
- **LIB**: ספרייה (40 places)

## 📅 Programme Scolaire par Niveau

### Grade 7 (כיתה ז)
- Hébreu: 5h/semaine
- Math: 5h/semaine
- Anglais: 4h/semaine
- Histoire juive: 2h/semaine
- Géographie: 2h/semaine
- Arts: 2h/semaine
- Éducation physique: 2h/semaine
- Torah: 3h/semaine

### Grade 8 (כיתה ח)
- + Biologie: 2h/semaine

### Grade 9 (כיתה ט)
- + Physique: 2h/semaine

### Grade 10 (כיתה י)
- Hébreu: 4h/semaine
- Math: 5h/semaine
- Anglais: 4h/semaine
- Histoire: 3h/semaine
- Physique: 3h/semaine
- Chimie: 3h/semaine
- Biologie: 2h/semaine
- Éducation physique: 2h/semaine
- Informatique: 2h/semaine

### Grades 11-12 (כיתה יא-יב)
- Focus scientifique renforcé
- Physique: 4h/semaine
- Informatique: 3h/semaine

## ⚙️ Contraintes Système

### Contraintes Dures (obligatoires)
1. **Pause déjeuner**: 12h-13h tous les jours
2. **Vendredi court**: Cours jusqu'à 13h seulement
3. **Pas de cours le samedi**: Respect du Shabbat
4. **Séparation des sexes**: Pour certaines matières religieuses et sport

### Contraintes Douces (préférentielles)
- Minimiser les trous dans l'emploi du temps
- Respecter les préférences des enseignants
- Équilibrer la charge quotidienne

## 🔧 Utilisation des Scripts

### Commandes Principales

```powershell
# Voir l'état actuel
python scripts/populate_test_data.py stats

# Peupler la base (interactive)
python scripts/populate_test_data.py populate

# Vider la base (interactive)
python scripts/populate_test_data.py clear

# Réinitialiser complètement (interactive)
python scripts/populate_test_data.py reset

# Mode force (sans confirmation)
python scripts/populate_test_data.py reset --force
```

### Configuration Environnement

```powershell
# Définir la base de données
$env:DATABASE_URL="sqlite:///./school_timetable.db"

# Puis utiliser les scripts
python scripts/populate_test_data.py stats
```

## 🔍 Vérification des Données

### API Teachers
```bash
# Lister tous les enseignants
GET /api/v1/teachers/

# Enseignant spécifique avec matières
GET /api/v1/teachers/1?include_subjects=true

# Disponibilités d'un enseignant
GET /api/v1/teachers/1/availability/
```

### API Subjects
```bash
# Lister toutes les matières
GET /api/v1/subjects/

# Matières religieuses
GET /api/v1/subjects/?subject_type=religious

# Matières nécessitant un labo
GET /api/v1/subjects/?requires_lab=true
```

## 📊 Statistiques de Test

- **Total relations**: 219 enregistrements
- **Utilisateurs**: 4 (admin, principal, coordinateur, secrétaire)
- **Enseignants**: 11 spécialisés
- **Matières**: 15 (bilingues)
- **Classes**: 12 (grades 7-12)
- **Salles**: 16 (standard + spécialisées)
- **Associations**: 17 enseignant-matière
- **Disponibilités**: 55 créneaux (5 jours × 11 enseignants)
- **Exigences**: 102 matière-classe
- **Contraintes**: 4 globales

## 🇮🇱 Spécificités Israéliennes

### Calendrier
- **Semaine scolaire**: Dimanche-Jeudi
- **Vendredi**: Journée courte (8h-13h)
- **Samedi**: Pas de cours (Shabbat)

### Matières Obligatoires
- **Hébreu**: Langue principale
- **Histoire juive**: Programme national
- **Torah/Talmud**: Selon le niveau religieux

### Contraintes Culturelles
- **Séparation des sexes**: Pour certaines matières
- **Respect du Shabbat**: Aucune activité le samedi
- **Pauses prayer**: Possibilité de pauses religieuses

## 🔄 Régénération des Données

Pour régénérer des données fraîches :

```powershell
# Nettoyer et recréer
python scripts/populate_test_data.py reset --force

# Vérifier le résultat
python scripts/populate_test_data.py stats
```

---

**💡 Conseil**: Les données sont cohérentes entre elles. Utilisez-les pour tester l'algorithme de génération d'emplois du temps avec des contraintes réalistes du système scolaire israélien. 