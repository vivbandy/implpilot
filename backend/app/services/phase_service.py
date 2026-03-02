"""Phase service: phase lifecycle and business logic."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.phase import Phase, PhaseName, PhaseStatus
from app.models.project import Project, CurrentPhase
from app.models.task import Task, TaskStatus
from app.schemas.phase import PhaseUpdate


# Default phase configuration
# Phases are created in this order for every new project
DEFAULT_PHASES = [
    {"name": PhaseName.KICKOFF, "display_name": "Kick-off", "order": 1, "status": PhaseStatus.ACTIVE},
    {"name": PhaseName.DESIGN, "display_name": "Design", "order": 2, "status": PhaseStatus.PENDING},
    {"name": PhaseName.IMPLEMENT, "display_name": "Implement", "order": 3, "status": PhaseStatus.PENDING},
    {"name": PhaseName.DEPLOY, "display_name": "Deploy", "order": 4, "status": PhaseStatus.PENDING},
]


async def create_default_phases(db: AsyncSession, project_id: UUID) -> list[Phase]:
    """
    Create the 4 default phases for a new project.

    This is called automatically after creating a project.
    The first phase (kickoff) is set to active by default.

    Args:
        db: Database session
        project_id: Project UUID

    Returns:
        List of created phase models
    """
    phases = []
    for phase_config in DEFAULT_PHASES:
        phase = Phase(
            project_id=project_id,
            name=phase_config["name"],
            display_name=phase_config["display_name"],
            order=phase_config["order"],
            status=phase_config["status"],
        )
        db.add(phase)
        phases.append(phase)

    await db.commit()
    for phase in phases:
        await db.refresh(phase)

    return phases


async def get_phase(db: AsyncSession, phase_id: UUID) -> Phase | None:
    """
    Get a phase by ID.

    Args:
        db: Database session
        phase_id: Phase UUID

    Returns:
        Phase model if found, None otherwise
    """
    result = await db.execute(
        select(Phase).where(Phase.id == phase_id)
    )
    return result.scalar_one_or_none()


async def get_project_phases(
    db: AsyncSession,
    project_id: UUID,
) -> list[Phase]:
    """
    Get all phases for a project, ordered by phase.order.

    Args:
        db: Database session
        project_id: Project UUID

    Returns:
        List of phase models ordered by order field
    """
    result = await db.execute(
        select(Phase)
        .where(Phase.project_id == project_id)
        .order_by(Phase.order)
    )
    return list(result.scalars().all())


async def update_phase(
    db: AsyncSession,
    phase_id: UUID,
    phase_data: PhaseUpdate,
) -> Phase | None:
    """
    Update a phase's dates or description.

    Note: Status changes are handled via complete_phase(), not here.

    Args:
        db: Database session
        phase_id: Phase UUID
        phase_data: Phase update data

    Returns:
        Updated phase model if found, None otherwise
    """
    phase = await get_phase(db, phase_id)
    if not phase:
        return None

    update_data = phase_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(phase, field, value)

    await db.commit()
    await db.refresh(phase)
    return phase


async def complete_phase(db: AsyncSession, phase_id: UUID) -> Phase | None:
    """
    Mark a phase as completed and activate the next phase.

    This function:
    1. Marks the current phase as completed with timestamp
    2. Finds the next phase (by order) and activates it
    3. Updates projects.current_phase to the new active phase
    4. Future: fires phase_completed notification

    Args:
        db: Database session
        phase_id: Phase UUID to complete

    Returns:
        Completed phase model if found, None otherwise
    """
    phase = await get_phase(db, phase_id)
    if not phase:
        return None

    # Mark phase as completed
    phase.status = PhaseStatus.COMPLETED
    phase.completed_at = datetime.utcnow()

    # Find next phase by order
    result = await db.execute(
        select(Phase)
        .where(
            Phase.project_id == phase.project_id,
            Phase.order > phase.order,
        )
        .order_by(Phase.order)
        .limit(1)
    )
    next_phase = result.scalar_one_or_none()

    # Activate next phase if it exists
    if next_phase:
        next_phase.status = PhaseStatus.ACTIVE
        next_phase.start_date = datetime.utcnow().date()

        # Update project's current_phase (denormalized field)
        project = await db.get(Project, phase.project_id)
        if project:
            # Map PhaseName to CurrentPhase enum
            phase_mapping = {
                PhaseName.KICKOFF: CurrentPhase.KICKOFF,
                PhaseName.DESIGN: CurrentPhase.DESIGN,
                PhaseName.IMPLEMENT: CurrentPhase.IMPLEMENT,
                PhaseName.DEPLOY: CurrentPhase.DEPLOY,
            }
            project.current_phase = phase_mapping.get(next_phase.name, CurrentPhase.KICKOFF)

    await db.commit()
    await db.refresh(phase)

    # TODO: Fire phase_completed notification (Step 11)

    return phase


async def get_phase_task_counts(
    db: AsyncSession,
    phase_id: UUID,
) -> dict[str, int]:
    """
    Get task counts for a phase.

    Returns counts for total, completed, in_progress, blocked, and overdue tasks.

    Args:
        db: Database session
        phase_id: Phase UUID

    Returns:
        Dictionary with task count statistics
    """
    # Total tasks (top-level only, excluding sub-tasks)
    total_result = await db.execute(
        select(func.count(Task.id))
        .where(Task.phase_id == phase_id, Task.parent_task_id.is_(None))
    )
    total = total_result.scalar() or 0

    # Completed tasks
    completed_result = await db.execute(
        select(func.count(Task.id))
        .where(
            Task.phase_id == phase_id,
            Task.parent_task_id.is_(None),
            Task.status == TaskStatus.COMPLETED,
        )
    )
    completed = completed_result.scalar() or 0

    # In progress tasks
    in_progress_result = await db.execute(
        select(func.count(Task.id))
        .where(
            Task.phase_id == phase_id,
            Task.parent_task_id.is_(None),
            Task.status == TaskStatus.IN_PROGRESS,
        )
    )
    in_progress = in_progress_result.scalar() or 0

    # Blocked tasks
    blocked_result = await db.execute(
        select(func.count(Task.id))
        .where(
            Task.phase_id == phase_id,
            Task.parent_task_id.is_(None),
            Task.status == TaskStatus.BLOCKED,
        )
    )
    blocked = blocked_result.scalar() or 0

    # Overdue tasks (due_date < today and not completed/cancelled)
    from datetime import date
    overdue_result = await db.execute(
        select(func.count(Task.id))
        .where(
            Task.phase_id == phase_id,
            Task.parent_task_id.is_(None),
            Task.due_date < date.today(),
            Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
        )
    )
    overdue = overdue_result.scalar() or 0

    return {
        "task_total": total,
        "task_completed": completed,
        "task_in_progress": in_progress,
        "task_blocked": blocked,
        "task_overdue": overdue,
    }
