"""CRUD Room."""

from app.api.api_v1.endpoints._crud import build_crud_router
from app.models import Room
from app.schemas import RoomCreate, RoomRead, RoomUpdate

router = build_crud_router(
    model=Room,
    create_schema=RoomCreate,
    update_schema=RoomUpdate,
    read_schema=RoomRead,
    entity_label="Salle",
)
