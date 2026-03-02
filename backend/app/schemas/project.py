"""Project Pydantic schemas."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.project import ProjectStatus, CurrentPhase


class ProjectBase(BaseModel):
    """Base project schema with common fields."""
    name: str
    customer_name: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    start_date: date | None = None
    target_end_date: date | None = None
    owner_id: UUID | None = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: str | None = None
    customer_name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    target_end_date: date | None = None
    actual_end_date: date | None = None
    owner_id: UUID | None = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: UUID
    status: ProjectStatus
    health_score: int | None
    current_phase: CurrentPhase
    start_date: date | None
    target_end_date: date | None
    actual_end_date: date | None
    owner_id: UUID | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectWithPhases(ProjectResponse):
    """Schema for project response with phases array."""
    phases: list["PhaseWithTaskCounts"]

    model_config = {"from_attributes": True}


# Forward reference for PhaseWithTaskCounts - will be resolved after importing
from app.schemas.phase import PhaseWithTaskCounts  # noqa: E402
ProjectWithPhases.model_rebuild()
