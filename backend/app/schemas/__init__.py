"""
Pydantic schemas for API data validation
"""

# Export all schemas for easy importing
from .common import (
    PaginationParams,
    PaginationResponse,
    ErrorResponse,
    SuccessResponse,
    PaginatedResponse,
    HealthCheckResponse,
    BulkOperationRequest,
    BulkOperationResponse,
)

from .teacher import (
    TeacherBase,
    TeacherCreate,
    TeacherUpdate,
    TeacherResponse,
    TeacherWithSubjects,
    TeacherBasic,
    TeacherAvailabilityBase,
    TeacherAvailabilityCreate,
    TeacherAvailability,
)

from .schedule import (
    ScheduleStatus,
    SolverStatus,
    ScheduleBase,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleEntryBase,
    ScheduleEntryCreate,
    ScheduleEntryUpdate,
    ScheduleEntryResponse,
    ScheduleConflictBase,
    ScheduleConflict,
    GenerateScheduleRequest,
    GenerateScheduleResponse,
    ClassGroupBasic,
    SubjectBasic,
    RoomBasic,
) 