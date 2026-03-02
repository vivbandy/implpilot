"""Phase Pydantic schemas."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.phase import PhaseName, PhaseStatus


class PhaseBase(BaseModel):
    """Base phase schema."""
    name: PhaseName
    display_name: str
    order: int


class PhaseUpdate(BaseModel):
    """Schema for updating a phase."""
    start_date: date | None = None
    target_end_date: date | None = None
    description: str | None = None
    # Note: status updates are handled via complete endpoint, not direct updates


class PhaseResponse(PhaseBase):
    """Schema for phase response."""
    id: UUID
    project_id: UUID
    status: PhaseStatus
    start_date: date | None
    target_end_date: date | None
    completed_at: datetime | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PhaseWithTaskCounts(PhaseResponse):
    """
    Schema for phase response with task counts.

    Used in project detail view to show phase progress.
    """
    task_total: int = 0
    task_completed: int = 0
    task_in_progress: int = 0
    task_blocked: int = 0
    task_overdue: int = 0

    model_config = {"from_attributes": True}
