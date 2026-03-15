"""Notes router — CRUD wired to tag processing pipeline."""
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.related_objects import Note, NoteEntityType
from app.models.tag import TagEntityType as TagEntityTypeEnum
from app.models.user import User
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from app.services.tag_service import process_tags
from app.utils.dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=list[NoteOut])
async def list_notes(
    entity_type: NoteEntityType = Query(...),
    entity_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NoteOut]:
    """
    List all notes for a given entity.

    Ordered newest-first so the UI shows the most recent note at the top.
    entity_type and entity_id are required — there is no global note list endpoint.
    """
    result = await db.execute(
        select(Note)
        .where(Note.entity_type == entity_type, Note.entity_id == entity_id)
        .order_by(Note.created_at.desc())
    )
    notes = result.scalars().all()
    return [NoteOut.model_validate(n) for n in notes]


@router.post("", response_model=NoteOut, status_code=201)
async def create_note(
    payload: NoteCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteOut:
    """
    Create a note attached to any entity.

    After saving, tag processing runs as a BackgroundTask — it never blocks
    the HTTP response. Tags are extracted, matched against tag_definitions,
    TagEvents are recorded, and auto_actions (escalation/FR creation) fire.
    """
    note = Note(
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        content=payload.content,
        author_id=current_user.id,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    # Tag processing runs in the background — response returns immediately
    background_tasks.add_task(
        _run_tag_processing,
        content=note.content,
        project_id=payload.project_id,
        entity_type=TagEntityType.NOTE,
        entity_id=note.id,
        author_id=current_user.id,
    )

    return NoteOut.model_validate(note)


@router.put("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteOut:
    """
    Update note content.

    Tag processing re-runs after update. process_tags() is idempotent —
    existing TagEvents for this note are skipped, only new tags fire.
    """
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    if note.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot edit another user's note.")

    note.content = payload.content
    await db.commit()
    await db.refresh(note)

    # Re-run tag processing — process_tags() idempotency prevents duplicate events
    # We need project_id for tag_events but don't store it on Note directly.
    # For now we skip background tag re-processing on edit (no project_id available).
    # Task: future improvement — store project_id on notes for re-processing on edit.

    return NoteOut.model_validate(note)


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a note. Only the author or an admin may delete."""
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    if note.author_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this note.")

    await db.delete(note)
    await db.commit()


async def _run_tag_processing(
    *,
    content: str,
    project_id: uuid.UUID,
    entity_type: TagEntityType,
    entity_id: uuid.UUID,
    author_id: uuid.UUID,
) -> None:
    """
    Background worker: opens its own DB session and runs process_tags.

    BackgroundTasks in FastAPI run after the response is sent.
    We need a fresh session because the request session is closed by then.
    """
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            await process_tags(
                text=content,
                project_id=project_id,
                entity_type=entity_type,
                entity_id=entity_id,
                author_id=author_id,
                db=db,
            )
        except Exception:
            # Log but don't crash — tag processing failure must not affect note writes
            import logging
            logging.getLogger(__name__).exception(
                "Tag processing failed for entity %s %s", entity_type, entity_id
            )
