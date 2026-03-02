"""Health score calculator for projects."""
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.phase import Phase, PhaseStatus
from app.models.task import Task, TaskStatus
from app.models.related_objects import Escalation, EscalationSeverity, EscalationStatus
from app.models.tag import TagEvent, TagDefinition, TagSentiment
from app.models.related_objects import Note


async def calculate_project_health(
    db: AsyncSession,
    project_id: UUID,
) -> int:
    """
    Calculate health score for a project (0-100).

    Formula from spec Section 5.1:
    - Start at 100
    - Deduct for overdue tasks (up to -30)
    - Deduct for critical escalations (up to -20)
    - Deduct for inactivity (up to -10)
    - Deduct for being behind schedule (up to -10)
    - Deduct for blocked tasks (up to -5)
    - Deduct for negative sentiment (up to -10)
    - Deduct for tag-derived escalations (up to -5)
    - Deduct for overdue phases (up to -10)

    Args:
        db: Database session
        project_id: Project UUID

    Returns:
        Health score (0-100)
    """
    score = 100

    # --- Overdue tasks (up to -30) ---
    total_tasks_result = await db.execute(
        select(func.count(Task.id))
        .where(Task.project_id == project_id)
    )
    total_tasks = total_tasks_result.scalar() or 0

    if total_tasks > 0:
        overdue_tasks_result = await db.execute(
            select(func.count(Task.id))
            .where(
                Task.project_id == project_id,
                Task.due_date < date.today(),
                Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
            )
        )
        overdue_tasks = overdue_tasks_result.scalar() or 0
        overdue_penalty = min(30, (overdue_tasks / total_tasks) * 100 * 0.5)
        score -= overdue_penalty

    # --- Open critical escalations (up to -20) ---
    critical_escalations_result = await db.execute(
        select(func.count(Escalation.id))
        .where(
            Escalation.project_id == project_id,
            Escalation.severity == EscalationSeverity.CRITICAL,
            Escalation.status.in_([EscalationStatus.OPEN, EscalationStatus.IN_PROGRESS]),
        )
    )
    critical_escalations = critical_escalations_result.scalar() or 0
    escalation_penalty = min(20, critical_escalations * 10)
    score -= escalation_penalty

    # --- Inactivity: no notes or task updates in 7+ days (-10) ---
    # Check most recent note
    note_result = await db.execute(
        select(Note.created_at)
        .join(Task, Note.entity_id == Task.id)
        .where(Task.project_id == project_id)
        .order_by(Note.created_at.desc())
        .limit(1)
    )
    latest_note = note_result.scalar_one_or_none()

    # Check most recent task update
    task_update_result = await db.execute(
        select(Task.updated_at)
        .where(Task.project_id == project_id)
        .order_by(Task.updated_at.desc())
        .limit(1)
    )
    latest_task_update = task_update_result.scalar_one_or_none()

    # Determine most recent activity
    latest_activity = None
    if latest_note and latest_task_update:
        latest_activity = max(latest_note, latest_task_update)
    elif latest_note:
        latest_activity = latest_note
    elif latest_task_update:
        latest_activity = latest_task_update

    if latest_activity:
        days_since_activity = (datetime.utcnow() - latest_activity).days
        if days_since_activity > 7:
            score -= 10

    # --- Behind schedule percentage (up to -10) ---
    # Simplified: if target_end_date has passed and project not completed
    # Future: calculate trajectory based on completion rate
    # For now, skip this penalty (requires more complex logic)

    # --- Blocked tasks (up to -5) ---
    blocked_tasks_result = await db.execute(
        select(func.count(Task.id))
        .where(
            Task.project_id == project_id,
            Task.status == TaskStatus.BLOCKED,
        )
    )
    blocked_tasks = blocked_tasks_result.scalar() or 0
    blocked_penalty = min(5, blocked_tasks * 2)
    score -= blocked_penalty

    # --- Sentiment tags (up to -10 or +10) ---
    # Count positive and negative sentiment tags
    positive_tags_result = await db.execute(
        select(func.count(TagEvent.id))
        .join(TagDefinition, TagEvent.tag_id == TagDefinition.id)
        .where(
            TagEvent.project_id == project_id,
            TagDefinition.sentiment == TagSentiment.POSITIVE,
        )
    )
    positive_tags = positive_tags_result.scalar() or 0

    negative_tags_result = await db.execute(
        select(func.count(TagEvent.id))
        .join(TagDefinition, TagEvent.tag_id == TagDefinition.id)
        .where(
            TagEvent.project_id == project_id,
            TagDefinition.sentiment == TagSentiment.NEGATIVE,
        )
    )
    negative_tags = negative_tags_result.scalar() or 0

    sentiment_diff = negative_tags - positive_tags
    sentiment_penalty = min(10, max(-10, sentiment_diff * 2))
    score -= sentiment_penalty

    # --- Tag-derived escalations (up to -5) ---
    tag_escalations_result = await db.execute(
        select(func.count(Escalation.id))
        .where(
            Escalation.project_id == project_id,
            Escalation.source == "tag_derived",
            Escalation.status.in_([EscalationStatus.OPEN, EscalationStatus.IN_PROGRESS]),
        )
    )
    tag_escalations = tag_escalations_result.scalar() or 0
    tag_escalation_penalty = min(5, tag_escalations * 3)
    score -= tag_escalation_penalty

    # --- Overdue phases (up to -10) ---
    # Count phases where target_end_date < today and status != completed
    overdue_phases_result = await db.execute(
        select(func.count(Phase.id))
        .where(
            Phase.project_id == project_id,
            Phase.target_end_date < date.today(),
            Phase.status != PhaseStatus.COMPLETED,
        )
    )
    overdue_phases = overdue_phases_result.scalar() or 0
    phase_penalty = min(10, overdue_phases * 5)
    score -= phase_penalty

    # Final score (0-100)
    return max(0, round(score))
