# API Subjects - Documentation Complète

## 📚 Vue d'ensemble

L'API Subjects fournit une gestion CRUD complète des matières scolaires avec support bilingue (français/hébreu). Elle prend en charge la recherche RTL, la validation des données, et l'intégration avec l'API Teachers.

## 🌟 Fonctionnalités principales

- **Support bilingue** : Noms et descriptions en français et hébreu
- **Validation robuste** : Codes uniques, heures cohérentes, noms obligatoires
- **Recherche avancée** : Filtres multilingues, par niveau, type, etc.
- **Intégration** : Relations many-to-many avec les enseignants
- **Support RTL** : Gestion des noms hébreux avec direction de texte
- **Statistiques** : Rapports détaillés sur les matières

## 📋 Modèle de données

### Champs principaux
```json
{
  "id": "integer (auto-généré)",
  "code": "string (unique, alphanumériqu, max 20 chars)",
  "nom_fr": "string (requis, max 255 chars)",
  "nom_he": "string (requis, max 255 chars)",
  "niveau_requis": "string (requis, ex: '6ème', '5ème')",
  "heures_semaine": "integer (1-40)",
  "type_matiere": "enum (obligatoire|optionnelle|specialisee)",
  "description_fr": "text (optionnel)",
  "description_he": "text (optionnel)"
}
```

### Champs de compatibilité
```json
{
  "requires_lab": "boolean",
  "requires_special_room": "boolean", 
  "requires_consecutive_hours": "boolean",
  "max_hours_per_day": "integer (1-8)",
  "is_religious": "boolean",
  "requires_gender_separation": "boolean"
}
```

## 🛠️ Endpoints disponibles

### 1. CRUD Principal

#### `GET /api/v1/subjects/`
Liste des matières avec filtres et pagination.

**Paramètres de requête :**
- `skip` : Nombre d'enregistrements à ignorer (défaut: 0)
- `limit` : Nombre maximum d'enregistrements (défaut: 100, max: 1000)
- `search` : Recherche dans les noms ou code
- `niveau` : Filtrer par niveau requis
- `type_matiere` : Filtrer par type (obligatoire/optionnelle/specialisee)
- `langue` : Préférence de langue pour la recherche (fr/he)
- `heures_min` : Heures minimum par semaine
- `heures_max` : Heures maximum par semaine
- `requires_lab` : Filtrer par exigence de laboratoire

**Exemple :**
```bash
GET /api/v1/subjects/?search=Math&langue=fr&niveau=6ème&type_matiere=obligatoire
```

#### `GET /api/v1/subjects/{id}`
Récupérer une matière spécifique avec les enseignants assignés.

**Réponse :**
```json
{
  "id": 1,
  "code": "MATH-6",
  "nom_fr": "Mathématiques",
  "nom_he": "מתמטיקה",
  "niveau_requis": "6ème",
  "heures_semaine": 4,
  "type_matiere": "obligatoire",
  "description_fr": "Cours de mathématiques pour la 6ème",
  "description_he": "שיעור מתמטיקה לכיתה ו'",
  "teachers": [
    {
      "id": 1,
      "first_name": "Jean",
      "last_name": "Dupont",
      "code": "T001"
    }
  ]
}
```

#### `POST /api/v1/subjects/`
Créer une nouvelle matière.

**Corps de requête :**
```json
{
  "code": "PHYS-6",
  "nom_fr": "Physique",
  "nom_he": "פיזיקה",
  "niveau_requis": "6ème",
  "heures_semaine": 3,
  "type_matiere": "obligatoire",
  "description_fr": "Cours de physique",
  "description_he": "שיעור פיזיקה",
  "requires_lab": true
}
```

#### `PUT /api/v1/subjects/{id}`
Mettre à jour une matière complètement.

#### `DELETE /api/v1/subjects/{id}`
Supprimer une matière avec vérifications.

**Paramètres :**
- `force` : Forcer la suppression même si des enseignants sont assignés

### 2. Recherche spécialisée

#### `GET /api/v1/subjects/search/`
Recherche avancée avec pagination.

**Paramètres :**
- `q` : Terme de recherche (requis)
- `langue` : Langue de recherche (fr/he)
- `page` : Numéro de page (défaut: 1)
- `per_page` : Éléments par page (défaut: 20, max: 100)

**Réponse :**
```json
{
  "subjects": [...],
  "total": 25,
  "page": 1,
  "per_page": 20,
  "total_pages": 2
}
```

#### `GET /api/v1/subjects/by-level/{level}`
Matières par niveau avec filtre de type optionnel.

**Exemple :**
```bash
GET /api/v1/subjects/by-level/6ème?type_matiere=obligatoire
```

### 3. Gestion des enseignants

#### `GET /api/v1/subjects/{id}/teachers`
Liste des enseignants assignés à une matière.

#### `POST /api/v1/subjects/{id}/teachers/{teacher_id}`
Assigner un enseignant à une matière.

#### `DELETE /api/v1/subjects/{id}/teachers/{teacher_id}`
Retirer un enseignant d'une matière.

### 4. Statistiques

#### `GET /api/v1/subjects/stats/summary`
Statistiques détaillées des matières.

**Réponse :**
```json
{
  "total_subjects": 15,
  "by_type": {
    "obligatoire": 8,
    "optionnelle": 5,
    "specialisee": 2
  },
  "by_level": {
    "6ème": 10,
    "5ème": 5
  },
  "hours_statistics": {
    "min_hours": 1,
    "max_hours": 6,
    "avg_hours": 3.2
  },
  "teacher_assignment": {
    "with_teachers": 12,
    "without_teachers": 3
  }
}
```

## ✅ Validation

### Règles de validation
- **code** : Alphanumériqu unique, 1-20 caractères
- **nom_fr/nom_he** : Obligatoires, non vides, max 255 caractères
- **heures_semaine** : Entre 1 et 40
- **type_matiere** : Doit être obligatoire, optionnelle, ou specialisee

### Exemples d'erreurs
```json
{
  "detail": [
    {
      "loc": ["body", "heures_semaine"],
      "msg": "ensure this value is less than or equal to 40",
      "type": "value_error.number.not_le",
      "ctx": {"limit_value": 40}
    }
  ]
}
```

## 🔒 Authentification

Tous les endpoints nécessitent une authentification Bearer Token.

**En-têtes requis :**
```
Authorization: Bearer <votre_token>
Content-Type: application/json
```

## 📝 Exemples d'utilisation

### Créer une matière bilingue
```python
import requests

headers = {"Authorization": "Bearer <token>"}
data = {
    "code": "HIST-6",
    "nom_fr": "Histoire",
    "nom_he": "היסטוריה",
    "niveau_requis": "6ème",
    "heures_semaine": 3,
    "type_matiere": "obligatoire"
}

response = requests.post(
    "http://localhost:8000/api/v1/subjects/",
    json=data,
    headers=headers
)
```

### Recherche multilingue
```python
# Recherche en français
response = requests.get(
    "http://localhost:8000/api/v1/subjects/?search=Math&langue=fr",
    headers=headers
)

# Recherche en hébreu
response = requests.get(
    "http://localhost:8000/api/v1/subjects/?search=מתמטיקה&langue=he",
    headers=headers
)
```

### Filtrage avancé
```python
# Matières obligatoires de 6ème avec laboratoire
response = requests.get(
    "http://localhost:8000/api/v1/subjects/?niveau=6ème&type_matiere=obligatoire&requires_lab=true",
    headers=headers
)
```

## 🔧 Support RTL

L'API prend en charge les noms hébreux avec direction de texte RTL :
- Les noms hébreux sont stockés correctement dans la base de données
- La recherche fonctionne en hébreu
- L'affichage respecte la direction RTL

## 🧪 Tests

Utilisez le script de test fourni :
```bash
python test_subjects_api.py
```

Le script teste :
- ✅ Création de matières bilingues
- ✅ Recherche multilingue
- ✅ Filtres par niveau et type
- ✅ Validation des données
- ✅ Endpoints de statistiques
- ✅ Gestion des enseignants

## 🚀 Integration avec Teachers API

L'API Subjects s'intègre parfaitement avec l'API Teachers :
- Relations many-to-many
- Assignation/retrait d'enseignants
- Consultation des enseignants par matière

## 📊 Cas d'usage typiques

1. **Gestion d'emploi du temps** : Récupérer les matières par niveau pour créer des plannings
2. **Recherche pédagogique** : Trouver des matières par type ou exigences spéciales
3. **Statistiques éducatives** : Analyser la répartition des heures et types de matières
4. **Interface bilingue** : Afficher les matières dans la langue préférée de l'utilisateur

## 🛡️ Sécurité

- Authentification obligatoire sur tous les endpoints
- Validation stricte des données d'entrée
- Codes uniques pour éviter les doublons
- Vérifications avant suppression

---

*Cette API respecte les standards RESTful et fournit une base solide pour la gestion des matières scolaires dans un environnement bilingue.* 