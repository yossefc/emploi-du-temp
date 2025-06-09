# APIs ClassGroups et Rooms - Documentation Complète

## Vue d'ensemble

Cette documentation couvre les APIs CRUD complètes pour la gestion des **Classes (ClassGroups)** et des **Salles (Rooms)** dans le système d'emploi du temps scolaire, avec logique métier avancée et validation croisée.

## 🎯 Modèles de Données

### ClassGroup (Classes)

```json
{
  "id": 1,
  "code": "6A",
  "nom": "Sixième A",
  "niveau": "6ème",
  "effectif": 28,
  "class_type": "regular",
  "description": "Classe de sixième générale",
  "academic_year": "2024-2025",
  "horaires_preferes": {
    "preferred_start": "08:00",
    "preferred_end": "16:00",
    "avoid_periods": ["12:00-13:00"]
  },
  "is_active": true,
  "primary_language": "fr",
  "homeroom_teacher_id": 5
}
```

### Room (Salles)

```json
{
  "id": 1,
  "code": "A101",
  "nom": "Salle de Math A101",
  "capacite": 35,
  "type_salle": "regular_classroom",
  "building": "Bâtiment A",
  "floor": 1,
  "equipements": {
    "projector": true,
    "whiteboard": true,
    "computers": false,
    "air_conditioning": true
  },
  "disponibilites": {
    "monday": ["08:00-16:00"],
    "tuesday": ["08:00-16:00"],
    "restrictions": ["12:00-13:00"]
  },
  "is_active": true,
  "is_bookable": true
}
```

## 📚 API ClassGroups

### Endpoints Principaux

#### 1. Liste des Classes
```http
GET /api/v1/classes/
```

**Paramètres de requête :**
- `skip` (int) : Nombre d'enregistrements à ignorer (pagination)
- `limit` (int) : Nombre maximum d'enregistrements à retourner
- `search` (str) : Recherche textuelle dans nom ou code
- `niveau` (str) : Filtrer par niveau (ex: "6ème", "5ème")
- `class_type` (str) : Type de classe (regular/advanced/special_needs)
- `min_effectif`/`max_effectif` (int) : Plage d'effectifs
- `academic_year` (str) : Année scolaire
- `is_active` (bool) : Statut actif/inactif

**Exemple de réponse :**
```json
[
  {
    "id": 1,
    "code": "6A",
    "nom": "Sixième A",
    "niveau": "6ème",
    "effectif": 28,
    "matieres_obligatoires": [
      {"id": 1, "code": "MATH", "nom_fr": "Mathématiques"},
      {"id": 2, "code": "FR", "nom_fr": "Français"}
    ],
    "homeroom_teacher": {
      "id": 5,
      "prenom": "Marie",
      "nom": "Dupont"
    }
  }
]
```

#### 2. Détail d'une Classe
```http
GET /api/v1/classes/{class_group_id}
```

#### 3. Création d'une Classe
```http
POST /api/v1/classes/
```

**Corps de la requête :**
```json
{
  "code": "6B",
  "nom": "Sixième B",
  "niveau": "6ème",
  "effectif": 30,
  "class_type": "regular",
  "description": "Classe de sixième avec option anglais renforcé",
  "academic_year": "2024-2025",
  "horaires_preferes": {
    "preferred_morning": true,
    "avoid_friday_afternoon": true
  },
  "subject_ids": [1, 2, 3, 4]
}
```

#### 4. Modification d'une Classe
```http
PUT /api/v1/classes/{class_group_id}
```

#### 5. Suppression d'une Classe
```http
DELETE /api/v1/classes/{class_group_id}
```

### Gestion des Matières

#### 1. Matières d'une Classe
```http
GET /api/v1/classes/{class_group_id}/subjects
```

#### 2. Assigner des Matières
```http
POST /api/v1/classes/{class_group_id}/subjects
```

**Corps de la requête :**
```json
{
  "subject_ids": [1, 2, 3]
}
```

#### 3. Retirer une Matière
```http
DELETE /api/v1/classes/{class_group_id}/subjects/{subject_id}
```

### Endpoints Spécialisés

#### 1. Classes par Niveau
```http
GET /api/v1/classes/by-level/{niveau}
```

#### 2. Vérification de Compatibilité Salle-Classe
```http
GET /api/v1/classes/capacity-check/{class_group_id}?room_id=123
```

**Réponse :**
```json
{
  "class_group_id": 1,
  "effectif": 28,
  "room_id": 123,
  "room_capacity": 35,
  "compatible": true,
  "capacity_difference": 7
}
```

#### 3. Statistiques des Classes
```http
GET /api/v1/classes/stats/summary
```

**Réponse :**
```json
{
  "total_classes": 24,
  "active_classes": 22,
  "by_type": {
    "regular": 18,
    "advanced": 4,
    "special_needs": 2
  },
  "by_level": {
    "6ème": 4,
    "5ème": 4,
    "4ème": 4,
    "3ème": 4
  },
  "student_statistics": {
    "total_students": 672,
    "avg_class_size": 28.0,
    "min_class_size": 24,
    "max_class_size": 32
  }
}
```

## 🏢 API Rooms

### Endpoints Principaux

#### 1. Liste des Salles
```http
GET /api/v1/rooms/
```

**Paramètres de requête :**
- `search` (str) : Recherche textuelle
- `type_salle` (str) : Type de salle
- `min_capacite`/`max_capacite` (int) : Plage de capacité
- `building` (str) : Bâtiment
- `floor` (int) : Étage
- `has_projector`/`has_computers`/`has_lab_equipment` (bool) : Équipements
- `is_active`/`is_bookable` (bool) : Statuts

#### 2. Détail d'une Salle
```http
GET /api/v1/rooms/{room_id}
```

#### 3. Création d'une Salle
```http
POST /api/v1/rooms/
```

**Corps de la requête :**
```json
{
  "code": "B205",
  "nom": "Laboratoire de Sciences B205",
  "capacite": 30,
  "type_salle": "science_lab",
  "building": "Bâtiment B",
  "floor": 2,
  "equipements": {
    "lab_equipment": true,
    "projector": true,
    "fume_hood": true,
    "safety_shower": true
  },
  "disponibilites": {
    "monday": ["08:00-16:00"],
    "tuesday": ["08:00-16:00"],
    "maintenance_slots": ["friday_17:00-18:00"]
  },
  "has_lab_equipment": true,
  "is_bookable": true
}
```

### Endpoints Spécialisés

#### 1. Salles Disponibles
```http
GET /api/v1/rooms/available/?day_of_week=1&start_time=08:00&end_time=09:00
```

**Paramètres :**
- `day_of_week` (int) : Jour (0=Dimanche, 5=Vendredi)
- `start_time`/`end_time` (str) : Créneaux horaires (format HH:MM)
- `min_capacity` (int) : Capacité minimale requise
- `required_equipment` (str) : Équipements requis (séparés par virgules)
- `room_type` (str) : Type de salle requis

#### 2. Salles par Capacité
```http
GET /api/v1/rooms/by-capacity/{min_capacity}
```

#### 3. Vérification des Conflits
```http
POST /api/v1/rooms/check-conflicts/
```

**Corps de la requête :**
```json
{
  "room_id": 123,
  "day_of_week": 1,
  "start_time": "08:00",
  "end_time": "09:00",
  "exclude_booking_id": 456
}
```

### Logique Métier Avancée

#### 1. Validation pour une Matière
```http
GET /api/v1/rooms/validate-for-subject/{subject_id}?class_effectif=28
```

**Réponse :**
```json
{
  "subject_id": 1,
  "subject_code": "PHYS",
  "subject_name_fr": "Physique",
  "requirements": {
    "needs_lab": true,
    "needs_special_room": true,
    "min_capacity": 28
  },
  "suitable_rooms_count": 3,
  "total_rooms_count": 15,
  "compatibility_rate": 20.0,
  "suitable_rooms": [
    {
      "id": 5,
      "code": "LAB1",
      "nom": "Laboratoire de Physique",
      "capacite": 30,
      "type_salle": "science_lab",
      "has_required_equipment": {
        "lab_equipment": true,
        "projector": true,
        "computers": false
      }
    }
  ]
}
```

#### 2. Suggestions d'Optimisation
```http
GET /api/v1/rooms/optimization/suggest
```

**Réponse :**
```json
{
  "total_rooms": 15,
  "bookable_rooms": 14,
  "utilization_rate": 93.3,
  "equipment_statistics": {
    "projector_coverage": 80.0,
    "computer_coverage": 40.0,
    "lab_coverage": 26.7
  },
  "optimization_suggestions": [
    {
      "type": "equipment",
      "priority": "high",
      "message": "Consider adding projectors to more rooms (12/15 have projectors)"
    }
  ]
}
```

#### 3. Statistiques des Salles
```http
GET /api/v1/rooms/stats/summary
```

## 🔄 Logique Métier et Validations

### Validations Automatiques

1. **Capacité vs Effectif :**
   - Vérification automatique que la capacité de la salle >= effectif de la classe
   - Alertes en cas d'incompatibilité

2. **Équipements Requis :**
   - Validation des équipements selon les exigences de la matière
   - Sciences → laboratoire requis
   - Informatique → ordinateurs requis

3. **Conflits de Réservation :**
   - Détection automatique des conflits horaires
   - Suggestions de créneaux alternatifs

4. **Cohérence des Données :**
   - Validation des codes uniques
   - Vérification des plages horaires
   - Contrôle des effectifs (1-50 étudiants)

### Optimisations

1. **Attribution Intelligente :**
   - Algorithme de suggestion salle/classe optimale
   - Prise en compte de la proximité géographique
   - Minimisation des déplacements

2. **Analyse d'Utilisation :**
   - Statistiques d'occupation des salles
   - Suggestions d'amélioration de l'efficacité
   - Détection des goulots d'étranglement

## 📊 Intégrations

### Avec l'API Teachers
- Association professeur principal/classe
- Vérification des compétences enseignant/matière

### Avec l'API Subjects  
- Relations many-to-many classe/matières
- Validation des prérequis par niveau
- Calcul automatique des heures hebdomadaires

### Avec l'API Schedules (future)
- Génération automatique d'emplois du temps
- Optimisation des créneaux
- Gestion des contraintes

## 🛡️ Sécurité et Authentification

Tous les endpoints nécessitent une authentification JWT valide via le header :
```
Authorization: Bearer <jwt_token>
```

## 📈 Codes de Statut HTTP

- **200** : Succès
- **201** : Création réussie
- **204** : Suppression réussie
- **400** : Erreur de validation
- **401** : Non authentifié
- **403** : Non autorisé
- **404** : Ressource non trouvée
- **409** : Conflit (ex: code déjà existant)

## 🚀 Exemples d'Utilisation

### Scénario Complet : Création d'une Classe avec Validation

```python
# 1. Créer une nouvelle classe
response = requests.post('/api/v1/classes/', json={
    "code": "5C",
    "nom": "Cinquième C",
    "niveau": "5ème", 
    "effectif": 26,
    "class_type": "regular"
})
class_id = response.json()['id']

# 2. Assigner les matières obligatoires
requests.post(f'/api/v1/classes/{class_id}/subjects', json={
    "subject_ids": [1, 2, 3, 4, 5]  # Math, Fr, Hist, Sci, Angl
})

# 3. Vérifier la compatibilité avec les salles
response = requests.get(f'/api/v1/classes/capacity-check/{class_id}')
compatible_rooms = response.json()['compatible_rooms']

# 4. Valider l'attribution pour chaque matière
for subject_id in [1, 2, 3, 4, 5]:
    response = requests.get(f'/api/v1/rooms/validate-for-subject/{subject_id}', 
                          params={'class_effectif': 26})
    print(f"Matière {subject_id}: {response.json()['suitable_rooms_count']} salles compatibles")
```

Cette documentation couvre l'ensemble des fonctionnalités des APIs ClassGroups et Rooms, permettant une gestion complète et optimisée des classes et salles dans votre système d'emploi du temps scolaire. 