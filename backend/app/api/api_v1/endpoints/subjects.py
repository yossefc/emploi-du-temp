"""CRUD Subject."""

from app.api.api_v1.endpoints._crud import build_crud_router
from app.models import Subject
from app.schemas import SubjectCreate, SubjectRead, SubjectUpdate

router = build_crud_router(
    model=Subject,
    create_schema=SubjectCreate,
    update_schema=SubjectUpdate,
    read_schema=SubjectRead,
    entity_label="Matière",
)
