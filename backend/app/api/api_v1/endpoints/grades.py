"""CRUD Grade."""

from app.api.api_v1.endpoints._crud import build_crud_router
from app.models import Grade
from app.schemas import GradeCreate, GradeRead, GradeUpdate

router = build_crud_router(
    model=Grade,
    create_schema=GradeCreate,
    update_schema=GradeUpdate,
    read_schema=GradeRead,
    entity_label="Niveau",
)
