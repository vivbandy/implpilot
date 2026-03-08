"""Pydantic schemas for Attachments."""
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.related_objects import AttachmentEntityType


class AttachmentCreate(BaseModel):
    entity_type: AttachmentEntityType
    entity_id: uuid.UUID
    label: str
    url: str


class AttachmentOut(BaseModel):
    id: uuid.UUID
    entity_type: AttachmentEntityType
    entity_id: uuid.UUID
    label: str
    url: str
    created_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
