"""Pydantic schemas for Tag definitions and events."""
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.tag import TagCategory, TagSentiment, TagAutoAction, TagEntityType


# ─── TagDefinition ─────────────────────────────────────────────────────────────

class TagDefinitionCreate(BaseModel):
    name: str
    category: TagCategory
    sentiment: TagSentiment | None = None
    auto_action: TagAutoAction = TagAutoAction.NONE
    description: str | None = None
    color: str | None = None


class TagDefinitionUpdate(BaseModel):
    category: TagCategory | None = None
    sentiment: TagSentiment | None = None
    auto_action: TagAutoAction | None = None
    description: str | None = None
    color: str | None = None


class TagDefinitionOut(BaseModel):
    id: uuid.UUID
    name: str
    category: TagCategory
    sentiment: TagSentiment | None
    auto_action: TagAutoAction
    description: str | None
    color: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── TagEvent ──────────────────────────────────────────────────────────────────

class TagEventOut(BaseModel):
    id: uuid.UUID
    tag_id: uuid.UUID
    project_id: uuid.UUID
    entity_type: TagEntityType
    entity_id: uuid.UUID
    author_id: uuid.UUID | None
    derived_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
