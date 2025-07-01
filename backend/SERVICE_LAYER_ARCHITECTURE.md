# Service Layer Architecture

Cette architecture implémente le pattern **Repository + Service** avec injection de dépendances et gestion d'erreurs robuste.

## 📁 Structure créée

```
backend/app/
├── core/
│   └── exceptions.py          # Exceptions personnalisées
├── repositories/
│   ├── __init__.py
│   ├── base.py               # BaseRepository générique
│   └── teacher_repository.py # Repository spécialisé pour Teacher
├── services/
│   ├── __init__.py
│   ├── base.py              # BaseService générique
│   └── teacher_service.py   # Service avec logique métier
└── examples/
    ├── __init__.py
    └── teacher_service_example.py # Exemples d'utilisation
```

## 🏗️ Architecture

### 1. **Exceptions personnalisées** (`core/exceptions.py`)
- `BaseAppException` : Exception de base
- `NotFoundException` : Ressource non trouvée
- `DuplicateException` : Ressource dupliquée
- `ValidationException` : Erreurs de validation
- `BusinessRuleException` : Violations de règles métier
- `PermissionException` : Problèmes de permissions
- `DatabaseException` : Erreurs de base de données
- `ConflictException` : Conflits d'état

### 2. **Repository Layer** (`repositories/`)

#### `BaseRepository<T>` - Repository générique
- **CRUD complet** : create, update, delete, get_by_id
- **Requêtes avancées** : get_by_filters, pagination, tri
- **Gestion d'erreurs** : Conversion des erreurs SQLAlchemy
- **Type safety** : Générique avec TypeVar

#### `TeacherRepository` - Repository spécialisé
- **Requêtes métier** : get_by_code, get_by_email, search_teachers
- **Filtres avancés** : par langue, matière, disponibilité
- **Opérations complexes** : assign_subjects, workload summaries
- **Performance** : joinedload pour relations

### 3. **Service Layer** (`services/`)

#### `BaseService<T>` - Service générique
- **Validation** : Méthodes abstraites validate_create/update_data
- **Règles métier** : _validate_business_rules_*
- **Gestion d'erreurs** : Wrapping des exceptions
- **Helpers** : _validate_required_fields, _validate_field_length

#### `TeacherService` - Service complet
- **Validation complète** : emails, téléphones, contraintes métier
- **Règles métier** : langues, horaires, contrats
- **Logique avancée** : assign_subjects, workload calculation
- **Gestion lifecycle** : activate/deactivate teachers

## 🔧 Utilisation

### Injection de dépendances
```python
from sqlalchemy.orm import Session
from app.repositories.teacher_repository import TeacherRepository
from app.services.teacher_service import TeacherService

def get_teacher_service(db: Session) -> TeacherService:
    teacher_repository = TeacherRepository(db)
    return TeacherService(teacher_repository)
```

### Création avec validation
```python
teacher_service = get_teacher_service(db)

teacher_data = {
    "code": "MATH001",
    "first_name": "Sarah",
    "last_name": "Cohen",
    "email": "sarah.cohen@school.edu",
    "max_hours_per_week": 25,
    "contract_type": "full_time"
}

try:
    teacher = teacher_service.create(teacher_data)
except ValidationException as e:
    print(f"Validation error: {e.message}")
except DuplicateException as e:
    print(f"Teacher already exists: {e.value}")
```

### Requêtes métier
```python
# Recherche intelligente
teachers = teacher_service.search_teachers("Cohen")

# Filtrage par capacités
bilingual_teachers = teacher_service.get_bilingual_teachers()
math_teachers = teacher_service.get_teachers_by_subject(subject_id=1)

# Pagination et tri
page = teacher_service.get_all(
    skip=0, limit=10, 
    order_by="last_name",
    filters={"is_active": True}
)
```

### Logique métier
```python
# Assignment avec validation
teacher_service.assign_subjects(teacher_id=1, subject_ids=[1, 2, 3])

# Workload analysis
workload = teacher_service.get_teacher_workload(teacher_id=1)
print(f"Utilisation: {workload['workload_percentage']}%")

# Désactivation sécurisée
teacher_service.deactivate_teacher(teacher_id=1, reason="End of contract")
```

## ✅ Avantages de cette architecture

### 🎯 **Séparation des responsabilités**
- **Repository** : Accès aux données uniquement
- **Service** : Logique métier et validation
- **Models** : Structure des données

### 🔒 **Gestion d'erreurs robuste**
- Exceptions typées et détaillées
- Messages d'erreur clairs
- Validation à plusieurs niveaux

### 📈 **Extensibilité**
- Base classes génériques réutilisables
- Pattern consistent pour tous les modèles
- Injection de dépendances facilitée

### 🧪 **Testabilité**
- Repositories mockables
- Services isolés
- Validation unitaire possible

### 🚀 **Performance**
- Requêtes optimisées avec joinedload
- Pagination intégrée
- Filtrage côté base de données

## 🔄 Extension pour autres modèles

Pour créer un service pour `Subject` :

1. **Repository** :
```python
class SubjectRepository(BaseRepository[Subject]):
    def get_by_code(self, code: str) -> Optional[Subject]:
        return self.get_by_field("code", code)
```

2. **Service** :
```python
class SubjectService(BaseService[Subject]):
    def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["code", "name_he", "name_fr"]
        self._validate_required_fields(data, required_fields)
        return data
    
    def validate_update_data(self, id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        return data
```

3. **Factory** :
```python
def get_subject_service(db: Session) -> SubjectService:
    subject_repository = SubjectRepository(Subject, db)
    return SubjectService(subject_repository)
```

## 📚 Exemples complets

Voir `app/examples/teacher_service_example.py` pour des exemples détaillés :
- Création et validation
- Gestion d'erreurs
- Pagination et filtrage
- Logique métier avancée

Cette architecture fournit une base solide, extensible et maintenable pour toute l'application ! 🎉 