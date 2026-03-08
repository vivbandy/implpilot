"""Pydantic schemas for Tasks."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.task import MatrixQuadrant, TaskPriority, TaskStatus


# ─── Task Create / Update ──────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: TaskPriority = TaskPriority.MEDIUM
    start_date: date | None = None
    due_date: date | None = None
    order: int = 0


class SubTaskCreate(BaseModel):
    """Used for POST /tasks/{id}/subtasks — phase_id is inherited from parent."""
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: TaskPriority = TaskPriority.MEDIUM
    start_date: date | None = None
    due_date: date | None = None
    order: int = 0


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    start_date: date | None = None
    due_date: date | None = None
    matrix_quadrant: MatrixQuadrant | None = None
    matrix_override: bool | None = None
    order: int | None = None


# ─── Task Out ─────────────────────────────────────────────────────────────────

class AssigneeOut(BaseModel):
    user_id: uuid.UUID

    model_config = {"from_attributes": True}


class TaskOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    phase_id: uuid.UUID
    parent_task_id: uuid.UUID | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    start_date: date | None
    due_date: date | None
    completed_at: datetime | None
    matrix_quadrant: MatrixQuadrant | None
    matrix_override: bool
    order: int
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    assignee_ids: list[uuid.UUID] = []
    sub_tasks: list["TaskOut"] = []

    model_config = {"from_attributes": True}


# ─── Matrix ───────────────────────────────────────────────────────────────────

class MatrixClassifyRequest(BaseModel):
    task_id: uuid.UUID


class MatrixClassifyResponse(BaseModel):
    task_id: uuid.UUID
    quadrant: MatrixQuadrant
    reasoning: str
