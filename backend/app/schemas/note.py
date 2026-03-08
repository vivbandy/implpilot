"""Pydantic schemas for Notes."""
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.related_objects import NoteEntityType


class NoteCreate(BaseModel):
    entity_type: NoteEntityType
    entity_id: uuid.UUID
    content: str
    # project_id is required so tag_service knows which project to associate events with
    project_id: uuid.UUID


class NoteUpdate(BaseModel):
    content: str


class NoteOut(BaseModel):
    id: uuid.UUID
    entity_type: NoteEntityType
    entity_id: uuid.UUID
    content: str
    author_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
