"""Tags router — tag definitions and events endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tag import TagDefinition
from app.models.user import User
from app.schemas.tag import TagDefinitionCreate, TagDefinitionOut, TagDefinitionUpdate, TagEventOut
from app.services import tag_service
from app.utils.dependencies import get_current_user

router = APIRouter()


@router.get("/definitions", response_model=list[TagDefinitionOut])
async def list_tag_definitions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TagDefinitionOut]:
    """Return all tag definitions ordered by category, then name."""
    tags = await tag_service.get_tag_definitions(db)
    return [TagDefinitionOut.model_validate(t) for t in tags]


@router.post("/definitions", response_model=TagDefinitionOut, status_code=201)
async def create_tag_definition(
    payload: TagDefinitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TagDefinitionOut:
    """
    Create a new tag definition.

    Tag names must be unique. Only admins should call this in practice
    (enforced at the UI layer; no role check here per MVP spec).
    """
    # Reject duplicate names
    existing = await db.execute(
        select(TagDefinition).where(TagDefinition.name == payload.name.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Tag '{payload.name}' already exists.")

    tag = TagDefinition(
        name=payload.name.lower(),  # normalize to lowercase
        category=payload.category,
        sentiment=payload.sentiment,
        auto_action=payload.auto_action,
        description=payload.description,
        color=payload.color,
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return TagDefinitionOut.model_validate(tag)


@router.put("/definitions/{tag_id}", response_model=TagDefinitionOut)
async def update_tag_definition(
    tag_id: uuid.UUID,
    payload: TagDefinitionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TagDefinitionOut:
    """Update a tag definition's metadata. Tag name cannot be changed (it's the lookup key)."""
    result = await db.execute(
        select(TagDefinition).where(TagDefinition.id == tag_id)
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag definition not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)

    await db.commit()
    await db.refresh(tag)
    return TagDefinitionOut.model_validate(tag)


@router.get("/events", response_model=list[TagEventOut])
async def list_tag_events(
    project_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TagEventOut]:
    """Return tag events. Optionally filter by project_id."""
    events = await tag_service.get_tag_events(db, project_id=project_id)
    return [TagEventOut.model_validate(e) for e in events]
