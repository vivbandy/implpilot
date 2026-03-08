"""
Tag service — process_tags() pipeline.

Design:
- Called as a FastAPI BackgroundTask after a note or task is saved.
  This means it never blocks the HTTP response.
- Pipeline: extract tags → resolve definitions → record TagEvents → fire auto_actions.
- Auto-actions: tags with auto_action='create_escalation' or 'create_feature_request'
  automatically create the corresponding object, linked to the source note/task.
- If the source entity is a task, its phase_id is copied to the created escalation/FR.
- Idempotent per entity: if a TagEvent already exists for (tag_id, entity_id), skip it.
  This prevents duplicate events if the same note/task is re-processed.
"""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import TagDefinition, TagEvent, TagEntityType, TagAutoAction
from app.models.related_objects import (
    Escalation,
    EscalationSource,
    EscalationStatus,
    EscalationSeverity,
    FeatureRequest,
    FeatureRequestSource,
    FeatureRequestStatus,
    FeatureRequestPriority,
    Note,
)
from app.models.task import Task
from app.utils.tag_parser import resolve_tags


async def process_tags(
    *,
    text: str,
    project_id: uuid.UUID,
    entity_type: TagEntityType,
    entity_id: uuid.UUID,
    author_id: uuid.UUID | None,
    db: AsyncSession,
) -> list[TagEvent]:
    """
    Full tag processing pipeline for a note or task.

    Steps:
    1. Extract #tags from text and resolve against tag_definitions.
    2. For each matched tag:
       a. Skip if a TagEvent already exists for (tag_id, entity_id) — idempotent.
       b. Create a TagEvent.
       c. If auto_action fires, create the derived escalation or feature request.
          Set derived_id on the TagEvent to link back to what was created.
    3. Commit all changes in one transaction.

    Returns the list of new TagEvents created.
    """
    resolved_tags = await resolve_tags(text, db)
    if not resolved_tags:
        return []

    # Load phase_id if the source entity is a task (needed for auto_action copies)
    task_phase_id: uuid.UUID | None = None
    if entity_type == TagEntityType.TASK:
        task_result = await db.execute(
            select(Task).where(Task.id == entity_id)
        )
        task = task_result.scalar_one_or_none()
        if task:
            task_phase_id = task.phase_id

    new_events: list[TagEvent] = []

    for tag_def in resolved_tags:
        # Idempotency check: skip if already processed this tag for this entity
        existing = await db.execute(
            select(TagEvent).where(
                TagEvent.tag_id == tag_def.id,
                TagEvent.entity_id == entity_id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Fire auto_action if configured — creates the derived object first
        # so we can set derived_id on the TagEvent
        derived_id: uuid.UUID | None = None

        if tag_def.auto_action == TagAutoAction.CREATE_ESCALATION:
            derived_id = await _create_escalation(
                tag_def=tag_def,
                project_id=project_id,
                phase_id=task_phase_id,
                entity_type=entity_type,
                entity_id=entity_id,
                author_id=author_id,
                db=db,
            )

        elif tag_def.auto_action == TagAutoAction.CREATE_FEATURE_REQUEST:
            derived_id = await _create_feature_request(
                tag_def=tag_def,
                project_id=project_id,
                phase_id=task_phase_id,
                entity_type=entity_type,
                entity_id=entity_id,
                author_id=author_id,
                db=db,
            )

        event = TagEvent(
            tag_id=tag_def.id,
            project_id=project_id,
            entity_type=entity_type,
            entity_id=entity_id,
            author_id=author_id,
            derived_id=derived_id,
        )
        db.add(event)
        new_events.append(event)

    await db.commit()
    return new_events


async def _create_escalation(
    *,
    tag_def: TagDefinition,
    project_id: uuid.UUID,
    phase_id: uuid.UUID | None,
    entity_type: TagEntityType,
    entity_id: uuid.UUID,
    author_id: uuid.UUID | None,
    db: AsyncSession,
) -> uuid.UUID:
    """
    Auto-create an escalation from a tag event.

    Links source_note_id if the entity is a note.
    Copies phase_id from the task if the entity is a task.
    """
    source_note_id = entity_id if entity_type == TagEntityType.NOTE else None
    task_id = entity_id if entity_type == TagEntityType.TASK else None

    escalation = Escalation(
        project_id=project_id,
        phase_id=phase_id,
        task_id=task_id,
        title=f"Auto-escalation: #{tag_def.name}",
        description=f"Auto-created from tag #{tag_def.name}.",
        severity=EscalationSeverity.MEDIUM,
        status=EscalationStatus.OPEN,
        source=EscalationSource.TAG_DERIVED,
        source_note_id=source_note_id,
        created_by=author_id,
    )
    db.add(escalation)
    await db.flush()  # get escalation.id without committing
    return escalation.id


async def _create_feature_request(
    *,
    tag_def: TagDefinition,
    project_id: uuid.UUID,
    phase_id: uuid.UUID | None,
    entity_type: TagEntityType,
    entity_id: uuid.UUID,
    author_id: uuid.UUID | None,
    db: AsyncSession,
) -> uuid.UUID:
    """
    Auto-create a feature request from a tag event.

    Links source_note_id if the entity is a note.
    Copies phase_id from the task if the entity is a task.
    """
    source_note_id = entity_id if entity_type == TagEntityType.NOTE else None
    task_id = entity_id if entity_type == TagEntityType.TASK else None

    fr = FeatureRequest(
        project_id=project_id,
        phase_id=phase_id,
        task_id=task_id,
        title=f"Auto-feature request: #{tag_def.name}",
        description=f"Auto-created from tag #{tag_def.name}.",
        priority=FeatureRequestPriority.MEDIUM,
        status=FeatureRequestStatus.OPEN,
        source=FeatureRequestSource.TAG_DERIVED,
        source_note_id=source_note_id,
        created_by=author_id,
    )
    db.add(fr)
    await db.flush()  # get fr.id without committing
    return fr.id


async def get_tag_definitions(db: AsyncSession) -> list[TagDefinition]:
    """Return all tag definitions ordered by category then name."""
    result = await db.execute(
        select(TagDefinition).order_by(TagDefinition.category, TagDefinition.name)
    )
    return list(result.scalars().all())


async def get_tag_events(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
) -> list[TagEvent]:
    """Return tag events, optionally filtered by project."""
    query = select(TagEvent).order_by(TagEvent.created_at.desc())
    if project_id:
        query = query.where(TagEvent.project_id == project_id)
    result = await db.execute(query)
    return list(result.scalars().all())
