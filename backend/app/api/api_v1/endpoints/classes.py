"""CRUD Class."""

from app.api.api_v1.endpoints._crud import build_crud_router
from app.models import Class
from app.schemas import ClassCreate, ClassRead, ClassUpdate

router = build_crud_router(
    model=Class,
    create_schema=ClassCreate,
    update_schema=ClassUpdate,
    read_schema=ClassRead,
    entity_label="Classe",
)
