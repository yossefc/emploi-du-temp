# Système ETL - Documentation

## Vue d'ensemble

Le système ETL (Extract, Transform, Load) permet l'importation complète de données depuis différentes sources vers le système de génération d'emplois du temps. Il a été conçu pour supporter l'import depuis le système Shahaf et d'autres formats de données.

## Architecture

### Structure des modules

```
backend/app/etl/
├── __init__.py              # Exports du module ETL
├── base_importer.py         # Classe de base pour tous les importateurs
├── shahaf_import.py         # Importateur spécifique pour Shahaf
├── exceptions.py            # Exceptions personnalisées
└── README.md               # Cette documentation
```

### Classe de base `BaseImporter`

La classe `BaseImporter` fournit les fonctionnalités communes à tous les importateurs :

- **Logging et traçabilité** : Suivi détaillé des imports
- **Gestion des erreurs** : Collecte et reporting des erreurs
- **Transactions** : Gestion des commits/rollbacks
- **Validation** : Méthodes de validation des données
- **Utilitaires** : Méthodes helper pour les opérations courantes

### Importateur Shahaf `ShahafImporter`

L'importateur principal qui hérite de `BaseImporter` et supporte :

- **Import JSON complet** : Depuis un export Shahaf complet
- **Import CSV par type** : Import individuel par type de données
- **Transformation des données** : Conversion des formats Shahaf vers le modèle interne
- **Validation des références** : Vérification des intégrités référentielles
- **Gestion des contraintes** : Import des contraintes et disponibilités

## Utilisation

### Import complet depuis JSON

```python
from app.etl.shahaf_import import ShahafImporter
from app.db.base import get_db

# Créer l'importateur
importer = ShahafImporter(db_session)

# Importer depuis un fichier JSON
result = importer.import_from_json('/path/to/export_shahaf.json')

# Vérifier le résultat
if result['total_errors'] == 0:
    print("Import réussi")
else:
    print(f"Import terminé avec {result['total_errors']} erreurs")
```

### Import CSV par type

```python
# Import des enseignants
result = importer.import_from_csv('/path/to/teachers.csv', 'teachers')

# Import des matières
result = importer.import_from_csv('/path/to/subjects.csv', 'subjects')

# Import des classes
result = importer.import_from_csv('/path/to/classes.csv', 'classes')

# Import des salles
result = importer.import_from_csv('/path/to/rooms.csv', 'rooms')
```

## Formats de données supportés

### Format JSON Shahaf

Structure attendue pour un export complet :

```json
{
  "subjects": [
    {
      "code": "MATH",
      "name_he": "מתמטיקה",
      "name_fr": "Mathématiques",
      "type": "academic",
      "requires_lab": false,
      "requires_consecutive_hours": true,
      "max_hours_per_day": 2,
      "color_hex": "#FF5733",
      "abbreviation": "MATH"
    }
  ],
  "rooms": [
    {
      "code": "A101",
      "name": "Salle A101",
      "capacity": 30,
      "type": "classroom",
      "building": "A",
      "floor": 1,
      "has_projector": true,
      "has_computers": false,
      "has_lab_equipment": false
    }
  ],
  "classes": [
    {
      "code": "6A",
      "name": "Sixième A",
      "grade_level": "6",
      "student_count": 28,
      "type": "regular",
      "is_mixed": true,
      "primary_language": "he",
      "academic_year": "2024-2025"
    }
  ],
  "teachers": [
    {
      "code": "T001",
      "first_name": "David",
      "last_name": "Cohen",
      "email": "david.cohen@school.edu",
      "phone": "+972-50-123-4567",
      "max_hours_per_week": 25,
      "max_hours_per_day": 6,
      "primary_language": "he",
      "can_teach_in_french": true,
      "can_teach_in_hebrew": true,
      "contract_type": "full_time",
      "subjects": ["MATH", "PHYS"],
      "availabilities": [
        {
          "day": "sunday",
          "start_time": "08:00",
          "end_time": "16:00",
          "is_available": true
        }
      ]
    }
  ],
  "constraints": [
    {
      "type": "class_subject_requirement",
      "class_code": "6A",
      "subject_code": "MATH",
      "hours_per_week": 5,
      "is_mandatory": true,
      "requires_double_period": false,
      "max_per_day": 2
    },
    {
      "type": "room_unavailability",
      "room_code": "A101",
      "day": "friday",
      "start_time": "12:00",
      "end_time": "13:00",
      "reason": "Prière du vendredi",
      "is_recurring": true
    }
  ]
}
```

### Format CSV pour les enseignants

| Colonne | Type | Obligatoire | Description |
|---------|------|-------------|-------------|
| code | string | Oui | Code unique de l'enseignant |
| first_name | string | Oui | Prénom |
| last_name | string | Oui | Nom de famille |
| email | string | Non | Adresse email |
| phone | string | Non | Téléphone |
| max_hours_per_week | integer | Non | Heures max par semaine (défaut: 30) |
| max_hours_per_day | integer | Non | Heures max par jour (défaut: 8) |
| primary_language | string | Non | Langue principale (he/fr, défaut: he) |
| can_teach_in_french | boolean | Non | Peut enseigner en français |
| can_teach_in_hebrew | boolean | Non | Peut enseigner en hébreu |
| contract_type | string | Non | Type de contrat (full_time/part_time/substitute) |
| subjects | string | Non | Matières séparées par des virgules |
| notes | string | Non | Notes supplémentaires |

### Format CSV pour les matières

| Colonne | Type | Obligatoire | Description |
|---------|------|-------------|-------------|
| code | string | Oui | Code unique de la matière |
| name_he | string | Oui | Nom en hébreu |
| name_fr | string | Oui | Nom en français |
| type | string | Non | Type (academic/sports/arts/religious/language/lab) |
| requires_lab | boolean | Non | Nécessite un laboratoire |
| requires_special_room | boolean | Non | Nécessite une salle spéciale |
| requires_consecutive_hours | boolean | Non | Nécessite des heures consécutives |
| max_hours_per_day | integer | Non | Heures max par jour (défaut: 2) |
| is_religious | boolean | Non | Matière religieuse |
| requires_gender_separation | boolean | Non | Nécessite séparation des genres |
| color_hex | string | Non | Couleur pour l'affichage (#RRGGBB) |
| abbreviation | string | Non | Abréviation (max 10 caractères) |

### Format CSV pour les classes

| Colonne | Type | Obligatoire | Description |
|---------|------|-------------|-------------|
| code | string | Oui | Code unique de la classe |
| name | string | Oui | Nom de la classe |
| grade_level | string | Oui | Niveau scolaire |
| student_count | integer | Oui | Nombre d'élèves |
| type | string | Non | Type (regular/advanced/special_needs) |
| is_boys_only | boolean | Non | Classe de garçons uniquement |
| is_girls_only | boolean | Non | Classe de filles uniquement |
| is_mixed | boolean | Non | Classe mixte (défaut: true) |
| primary_language | string | Non | Langue principale (he/fr, défaut: he) |
| description | string | Non | Description |
| academic_year | string | Non | Année scolaire (défaut: 2024-2025) |

### Format CSV pour les salles

| Colonne | Type | Obligatoire | Description |
|---------|------|-------------|-------------|
| code | string | Oui | Code unique de la salle |
| name | string | Oui | Nom de la salle |
| capacity | integer | Oui | Capacité maximale |
| type | string | Non | Type de salle (classroom/lab/gym/etc.) |
| building | string | Non | Nom/numéro du bâtiment |
| floor | integer | Non | Étage |
| has_projector | boolean | Non | Dispose d'un projecteur |
| has_computers | boolean | Non | Dispose d'ordinateurs |
| has_lab_equipment | boolean | Non | Dispose d'équipement de laboratoire |
| has_air_conditioning | boolean | Non | Dispose de climatisation |
| is_accessible | boolean | Non | Accessible aux personnes handicapées |
| suitable_for_prayer | boolean | Non | Appropriée pour la prière |
| gender_restricted | string | Non | Restriction de genre (boys/girls) |
| description | string | Non | Description |

## Endpoints API

### Import complet Shahaf

```http
POST /api/v1/import/import-complete-shahaf
Content-Type: multipart/form-data

file: export_shahaf.json
```

### Import par type de données

```http
POST /api/v1/import/import-subjects
Content-Type: multipart/form-data

file: subjects.csv
```

```http
POST /api/v1/import/import-classes
Content-Type: multipart/form-data

file: classes.csv
```

```http
POST /api/v1/import/import-rooms
Content-Type: multipart/form-data

file: rooms.csv
```

```http
POST /api/v1/import/import-enhanced-teachers
Content-Type: multipart/form-data

file: teachers.csv
```

### Validation des données

```http
POST /api/v1/import/validate-import-data
Content-Type: multipart/form-data

file: data.csv
data_type: teachers|subjects|classes|rooms
```

## Gestion des erreurs

Le système ETL utilise une hiérarchie d'exceptions personnalisées :

- **`ETLError`** : Exception de base avec support des numéros de ligne
- **`ValidationError`** : Erreurs de validation des données
- **`TransformationError`** : Erreurs lors de la transformation
- **`ReferenceError`** : Erreurs de références croisées
- **`ImportError`** : Erreurs lors de l'import en base

### Exemple de gestion d'erreur

```python
try:
    result = importer.import_from_json(file_path)
except ValidationError as e:
    print(f"Erreur de validation ligne {e.line_number}: {e.message}")
except ETLError as e:
    print(f"Erreur ETL: {e}")
```

## Fonctionnalités avancées

### Validation des références croisées

Le système valide automatiquement :
- Les références enseignants → matières
- Les références classes → matières (exigences)
- Les références contraintes → entités

### Gestion des imports incrémentaux

Le système supporte la mise à jour des données existantes :
- Utilisation de `get_or_create_record()` pour éviter les doublons
- Mise à jour des champs modifiés
- Préservation des relations existantes

### Logging et monitoring

Chaque import génère des logs détaillés :
- Heure de début et fin
- Nombre d'enregistrements traités
- Taux de succès
- Liste des erreurs et avertissements

## Bonnes pratiques

### Ordre d'import recommandé

1. **Matières** : Doivent être importées en premier
2. **Salles** : Indépendantes des autres entités
3. **Classes** : Peuvent référencer des matières
4. **Enseignants** : Peuvent référencer des matières
5. **Contraintes** : Doivent être importées en dernier

### Préparation des données

- Vérifier l'unicité des codes
- Valider les formats de données
- Nettoyer les données avant import
- Utiliser l'endpoint de validation

### Gestion des erreurs

- Toujours vérifier le résultat d'import
- Examiner les logs d'erreur
- Corriger les données source si nécessaire
- Recommencer l'import après correction

## Extensibilité

Le système peut être étendu pour supporter d'autres sources :

1. **Créer une classe héritant de `BaseImporter`**
2. **Implémenter les méthodes abstraites** :
   - `validate_data()`
   - `transform_data()`
   - `import_data()`
3. **Ajouter des méthodes de transformation spécifiques**
4. **Créer les endpoints API correspondants**

## Dépannage

### Problèmes courants

1. **Erreurs de référence** : Vérifier l'ordre d'import
2. **Doublons** : Utiliser des codes uniques
3. **Formats de données** : Vérifier les types et formats
4. **Contraintes de base** : Vérifier les validations du modèle

### Logs utiles

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.etl")
```

### Mode debug

```python
importer = ShahafImporter(db)
importer.debug = True  # Active les logs détaillés
``` 