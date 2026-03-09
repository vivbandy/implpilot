"""Pydantic schemas for Feature Requests, Escalations, and Contacts."""
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.related_objects import (
    EscalationSeverity,
    EscalationSource,
    EscalationStatus,
    FeatureRequestPriority,
    FeatureRequestSource,
    FeatureRequestStatus,
)


# ─── Feature Requests ─────────────────────────────────────────────────────────

class FeatureRequestCreate(BaseModel):
    title: str
    description: str | None = None
    why_important: str | None = None
    priority: FeatureRequestPriority = FeatureRequestPriority.MEDIUM
    phase_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    requested_by: str | None = None


class FeatureRequestUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    why_important: str | None = None
    priority: FeatureRequestPriority | None = None
    status: FeatureRequestStatus | None = None
    phase_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    requested_by: str | None = None


class FeatureRequestOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    phase_id: uuid.UUID | None
    task_id: uuid.UUID | None
    title: str
    description: str | None
    why_important: str | None
    priority: FeatureRequestPriority
    status: FeatureRequestStatus
    requested_by: str | None
    source: FeatureRequestSource
    source_note_id: uuid.UUID | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Escalations ──────────────────────────────────────────────────────────────

class EscalationCreate(BaseModel):
    title: str
    description: str | None = None
    severity: EscalationSeverity = EscalationSeverity.MEDIUM
    phase_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    raised_by: str | None = None


class EscalationUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: EscalationSeverity | None = None
    status: EscalationStatus | None = None
    phase_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    raised_by: str | None = None


class EscalationOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    phase_id: uuid.UUID | None
    task_id: uuid.UUID | None
    title: str
    description: str | None
    severity: EscalationSeverity
    status: EscalationStatus
    raised_by: str | None
    source: EscalationSource
    source_note_id: uuid.UUID | None
    resolved_at: datetime | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Contacts ─────────────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    name: str
    email: str | None = None
    role: str | None = None
    company: str | None = None
    is_primary: bool = False


class ContactUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None
    company: str | None = None
    is_primary: bool | None = None


class ContactOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    email: str | None
    role: str | None
    company: str | None
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}
