"""External tickets router — URL-based ticket linking (Jira, Zendesk, other)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.related_objects import ExternalTicket, ExternalTicketEntityType
from app.models.user import User
from app.schemas.external_ticket import ExternalTicketCreate, ExternalTicketOut, ExternalTicketUpdate
from app.utils.dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=list[ExternalTicketOut])
async def list_external_tickets(
    entity_type: ExternalTicketEntityType = Query(...),
    entity_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExternalTicketOut]:
    """
    List all external ticket links for a given entity.

    entity_type and entity_id are required query params.
    No global list — tickets are always fetched per entity.
    """
    result = await db.execute(
        select(ExternalTicket)
        .where(
            ExternalTicket.entity_type == entity_type,
            ExternalTicket.entity_id == entity_id,
        )
        .order_by(ExternalTicket.created_at.asc())
    )
    tickets = result.scalars().all()
    return [ExternalTicketOut.model_validate(t) for t in tickets]


@router.post("", response_model=ExternalTicketOut, status_code=201)
async def create_external_ticket(
    payload: ExternalTicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExternalTicketOut:
    """
    Link an external ticket (Jira, Zendesk, etc.) to a task, feature request, or escalation.

    MVP: URL-only, no live sync. status_cache is updated manually.
    """
    ticket = ExternalTicket(
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        ticket_system=payload.ticket_system,
        ticket_id=payload.ticket_id,
        url=payload.url,
        label=payload.label,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ExternalTicketOut.model_validate(ticket)


@router.put("/{ticket_id}", response_model=ExternalTicketOut)
async def update_external_ticket(
    ticket_id: uuid.UUID,
    payload: ExternalTicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExternalTicketOut:
    """Update ticket metadata or status_cache."""
    result = await db.execute(
        select(ExternalTicket).where(ExternalTicket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="External ticket not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    await db.commit()
    await db.refresh(ticket)
    return ExternalTicketOut.model_validate(ticket)


@router.delete("/{ticket_id}", status_code=204)
async def delete_external_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove an external ticket link."""
    result = await db.execute(
        select(ExternalTicket).where(ExternalTicket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="External ticket not found.")

    await db.delete(ticket)
    await db.commit()
