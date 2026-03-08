"""Pydantic schemas for External Tickets."""
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.related_objects import ExternalTicketEntityType, ExternalTicketSystem


class ExternalTicketCreate(BaseModel):
    entity_type: ExternalTicketEntityType
    entity_id: uuid.UUID
    ticket_system: ExternalTicketSystem
    ticket_id: str | None = None
    url: str
    label: str | None = None


class ExternalTicketUpdate(BaseModel):
    ticket_id: str | None = None
    url: str | None = None
    label: str | None = None
    status_cache: str | None = None


class ExternalTicketOut(BaseModel):
    id: uuid.UUID
    entity_type: ExternalTicketEntityType
    entity_id: uuid.UUID
    ticket_system: ExternalTicketSystem
    ticket_id: str | None
    url: str
    label: str | None
    status_cache: str | None
    last_synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
