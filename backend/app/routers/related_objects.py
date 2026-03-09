"""
Related objects router — Feature Requests, Escalations, Contacts.

All list/create endpoints are scoped under /projects/{project_id}/...
All update/delete endpoints are at the top-level resource path.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.related_objects import (
    Contact,
    Escalation,
    EscalationSource,
    EscalationStatus,
    FeatureRequest,
    FeatureRequestSource,
)
from app.models.user import User
from app.schemas.related_objects import (
    ContactCreate,
    ContactOut,
    ContactUpdate,
    EscalationCreate,
    EscalationOut,
    EscalationUpdate,
    FeatureRequestCreate,
    FeatureRequestOut,
    FeatureRequestUpdate,
)
from app.utils.dependencies import get_current_user

router = APIRouter()


# ─── Feature Requests ─────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/feature-requests", response_model=list[FeatureRequestOut])
async def list_feature_requests(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FeatureRequestOut]:
    """List all feature requests for a project, newest first."""
    result = await db.execute(
        select(FeatureRequest)
        .where(FeatureRequest.project_id == project_id)
        .order_by(FeatureRequest.created_at.desc())
    )
    return [FeatureRequestOut.model_validate(fr) for fr in result.scalars().all()]


@router.post("/projects/{project_id}/feature-requests", response_model=FeatureRequestOut, status_code=201)
async def create_feature_request(
    project_id: uuid.UUID,
    payload: FeatureRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeatureRequestOut:
    """Create a feature request manually. Source is always 'manual' here — tag-derived ones are created by tag_service."""
    fr = FeatureRequest(
        project_id=project_id,
        phase_id=payload.phase_id,
        task_id=payload.task_id,
        title=payload.title,
        description=payload.description,
        why_important=payload.why_important,
        priority=payload.priority,
        requested_by=payload.requested_by,
        source=FeatureRequestSource.MANUAL,
        created_by=current_user.id,
    )
    db.add(fr)
    await db.commit()
    await db.refresh(fr)
    return FeatureRequestOut.model_validate(fr)


@router.put("/feature-requests/{fr_id}", response_model=FeatureRequestOut)
async def update_feature_request(
    fr_id: uuid.UUID,
    payload: FeatureRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeatureRequestOut:
    """Update a feature request's fields or status."""
    result = await db.execute(select(FeatureRequest).where(FeatureRequest.id == fr_id))
    fr = result.scalar_one_or_none()
    if not fr:
        raise HTTPException(status_code=404, detail="Feature request not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(fr, field, value)

    await db.commit()
    await db.refresh(fr)
    return FeatureRequestOut.model_validate(fr)


@router.delete("/feature-requests/{fr_id}", status_code=204)
async def delete_feature_request(
    fr_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a feature request."""
    result = await db.execute(select(FeatureRequest).where(FeatureRequest.id == fr_id))
    fr = result.scalar_one_or_none()
    if not fr:
        raise HTTPException(status_code=404, detail="Feature request not found.")

    await db.delete(fr)
    await db.commit()


# ─── Escalations ──────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/escalations", response_model=list[EscalationOut])
async def list_escalations(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EscalationOut]:
    """List all escalations for a project, newest first."""
    result = await db.execute(
        select(Escalation)
        .where(Escalation.project_id == project_id)
        .order_by(Escalation.created_at.desc())
    )
    return [EscalationOut.model_validate(e) for e in result.scalars().all()]


@router.post("/projects/{project_id}/escalations", response_model=EscalationOut, status_code=201)
async def create_escalation(
    project_id: uuid.UUID,
    payload: EscalationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EscalationOut:
    """Create an escalation manually. Source is always 'manual' here — tag-derived ones are created by tag_service."""
    escalation = Escalation(
        project_id=project_id,
        phase_id=payload.phase_id,
        task_id=payload.task_id,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        raised_by=payload.raised_by,
        source=EscalationSource.MANUAL,
        created_by=current_user.id,
    )
    db.add(escalation)
    await db.commit()
    await db.refresh(escalation)
    return EscalationOut.model_validate(escalation)


@router.put("/escalations/{escalation_id}", response_model=EscalationOut)
async def update_escalation(
    escalation_id: uuid.UUID,
    payload: EscalationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EscalationOut:
    """
    Update an escalation.

    Setting status to 'resolved' or 'closed' automatically stamps resolved_at.
    """
    result = await db.execute(select(Escalation).where(Escalation.id == escalation_id))
    escalation = result.scalar_one_or_none()
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found.")

    update_data = payload.model_dump(exclude_unset=True)

    # Stamp resolved_at when transitioning to resolved/closed
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status in (EscalationStatus.RESOLVED, EscalationStatus.CLOSED):
            if escalation.resolved_at is None:
                escalation.resolved_at = datetime.utcnow()
        else:
            escalation.resolved_at = None

    for field, value in update_data.items():
        setattr(escalation, field, value)

    await db.commit()
    await db.refresh(escalation)
    return EscalationOut.model_validate(escalation)


# ─── Contacts ─────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/contacts", response_model=list[ContactOut])
async def list_contacts(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ContactOut]:
    """List all contacts for a project. Primary contact is returned first."""
    result = await db.execute(
        select(Contact)
        .where(Contact.project_id == project_id)
        .order_by(Contact.is_primary.desc(), Contact.created_at)
    )
    return [ContactOut.model_validate(c) for c in result.scalars().all()]


@router.post("/projects/{project_id}/contacts", response_model=ContactOut, status_code=201)
async def create_contact(
    project_id: uuid.UUID,
    payload: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContactOut:
    """Add a contact to a project."""
    contact = Contact(
        project_id=project_id,
        name=payload.name,
        email=payload.email,
        role=payload.role,
        company=payload.company,
        is_primary=payload.is_primary,
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return ContactOut.model_validate(contact)


@router.put("/contacts/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: uuid.UUID,
    payload: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContactOut:
    """Update a contact."""
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)

    await db.commit()
    await db.refresh(contact)
    return ContactOut.model_validate(contact)


@router.delete("/contacts/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a contact."""
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")

    await db.delete(contact)
    await db.commit()
