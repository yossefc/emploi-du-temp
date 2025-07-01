# Simplified Timetable Solver

## Vue d'ensemble

Le `SimplifiedTimetableSolver` est une version corrigée et simplifiée du solver d'emploi du temps qui résout les problèmes critiques identifiés dans l'implémentation originale.

## Problèmes corrigés

### 1. **Incohérences des modèles**
- ✅ Utilise `day_of_week.value` au lieu de `day` inexistant
- ✅ Gère correctement les champs de compatibilité (`student_count`/`effectif`, `capacity`/`capacite`)
- ✅ Supprime les références à `subject.room_type` qui n'existe pas

### 2. **Logique de solver**
- ✅ Conversion temps-période simplifiée et robuste
- ✅ Création de variables filtrées intelligemment
- ✅ Contraintes essentielles implémentées correctement
- ✅ Pas d'objectif de minimisation complexe (juste satisfaction des contraintes)

### 3. **Architecture**
- ✅ Structure modulaire claire
- ✅ Gestion d'erreurs complète
- ✅ Logs détaillés pour le débogage
- ✅ Validation des données d'entrée

## Utilisation

### Basic Usage

```python
from sqlalchemy.orm import Session
from app.solver.simplified_solver import SimplifiedTimetableSolver

# Créer une session de base de données
db = get_db_session()

# Initialiser le solver
solver = SimplifiedTimetableSolver(db)

# Résoudre avec limite de temps
result = solver.solve(time_limit_seconds=300)

# Vérifier le résultat
if result['status'] in ['optimal', 'feasible']:
    print(f"Solution trouvée avec {len(result['assignments'])} assignations")
    for assignment in result['assignments'][:5]:  # Afficher les 5 premières
        print(f"Classe {assignment['class_id']} - {assignment['day']} période {assignment['period']}")
else:
    print(f"Aucune solution: {result['status']}")
    for error in result.get('errors', []):
        print(f"Erreur: {error}")
```

### Structure du résultat

```python
{
    'status': 'optimal' | 'feasible' | 'infeasible' | 'invalid_data' | 'no_variables',
    'assignments': [
        {
            'class_id': int,
            'day': str,              # 'sunday', 'monday', etc.
            'day_index': int,        # 0-5
            'period': int,           # 0-7 (0-5 pour vendredi)
            'teacher_id': int,
            'subject_id': int,
            'room_id': int,
            'start_time': str,       # 'HH:MM'
            'end_time': str          # 'HH:MM'
        }
    ],
    'solution_time': float,          # temps en secondes
    'conflicts': [],                 # conflits détectés
    'statistics': {
        'num_variables': int,
        'num_branches': int,
        'num_conflicts': int,
        'wall_time': float
    }
}
```

## Contraintes implémentées

### 1. **Contraintes de conflit**
- Une classe ne peut avoir qu'un cours à la fois
- Un enseignant ne peut enseigner qu'une classe à la fois  
- Une salle ne peut accueillir qu'une classe à la fois

### 2. **Contraintes de besoins**
- Respecter le nombre d'heures requis par matière et classe
- Respecter les heures maximales par semaine des enseignants

### 3. **Contraintes de disponibilité**
- Respecter les disponibilités des enseignants
- Respecter les disponibilités des salles
- Vendredi se termine à 13h (période 6)

### 4. **Contraintes de capacité**
- Vérifier que la salle peut accueillir le nombre d'étudiants
- Vérifier que l'enseignant peut enseigner la matière

## Débogage

Le solver utilise des logs détaillés :

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Les logs incluent :
# - Chargement des données
# - Création des variables
# - Ajout des contraintes
# - Progrès de résolution
# - Validation de la solution
```

## Test

Utilisez le script de test fourni :

```bash
cd backend
python test_simplified_solver.py
```

## Limitations actuelles

1. **Pas d'optimisation** : Le solver cherche juste une solution faisable
2. **Pas de contraintes avancées** : Pas de gestion des gaps, préférences, etc.
3. **Pas de contraintes religieuses** : Prière du vendredi, séparation des genres, etc.

## Prochaines étapes

1. Ajouter des contraintes de préférence (soft constraints)
2. Implémenter la minimisation des gaps dans l'emploi du temps
3. Ajouter des contraintes spécifiques au contexte israélien
4. Optimiser les performances pour de grandes instances 