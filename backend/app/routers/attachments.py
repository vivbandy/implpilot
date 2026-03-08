"""Attachments router — URL-based attachment CRUD."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.related_objects import Attachment
from app.models.user import User
from app.schemas.attachment import AttachmentCreate, AttachmentOut
from app.utils.dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=AttachmentOut, status_code=201)
async def create_attachment(
    payload: AttachmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttachmentOut:
    """
    Attach a URL to any entity (project, phase, task, feature_request, escalation).

    MVP: URL-only. No file upload (S3 is out of scope for MVP).
    """
    attachment = Attachment(
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        label=payload.label,
        url=payload.url,
        created_by=current_user.id,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return AttachmentOut.model_validate(attachment)


@router.delete("/{attachment_id}", status_code=204)
async def delete_attachment(
    attachment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an attachment. Only the creator or an admin may delete."""
    result = await db.execute(
        select(Attachment).where(Attachment.id == attachment_id)
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found.")
    if attachment.created_by != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this attachment.")

    await db.delete(attachment)
    await db.commit()
