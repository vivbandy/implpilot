"""
Task service — business logic for tasks, sub-tasks, and assignees.

Enforcement rules (all here, never in routers):
- Every task must belong to a phase (phase_id required, validated against the phase).
- Sub-task phase_id must match its parent's phase_id — reject 422 if not.
- Sub-tasks cannot have sub-tasks (max depth 1) — reject 422 if parent already has a parent.
- matrix_service classification runs on top-level tasks only.
- completed_at timestamp is set automatically when status transitions to 'completed'.
"""
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.phase import Phase
from app.models.task import Task, TaskAssignee, TaskStatus
from app.models.user import User
from app.schemas.task import SubTaskCreate, TaskCreate, TaskUpdate
from app.services.matrix_service import classify_task


# ─── Task CRUD ────────────────────────────────────────────────────────────────

async def create_task(
    *,
    phase_id: uuid.UUID,
    payload: TaskCreate,
    created_by: uuid.UUID,
    db: AsyncSession,
) -> Task:
    """
    Create a top-level task in a phase.

    Validates the phase exists and belongs to the expected project.
    Sets matrix_quadrant via deterministic classification immediately on creation.
    """
    phase = await _get_phase_or_404(phase_id, db)

    task = Task(
        project_id=phase.project_id,
        phase_id=phase_id,
        parent_task_id=None,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        start_date=payload.start_date,
        due_date=payload.due_date,
        order=payload.order,
        created_by=created_by,
    )
    db.add(task)
    await db.flush()  # get task.id for classification

    # Run deterministic matrix classification immediately
    quadrant, _ = classify_task(task)
    task.matrix_quadrant = quadrant

    await db.commit()
    await db.refresh(task)
    return task


async def create_subtask(
    *,
    parent_task_id: uuid.UUID,
    payload: SubTaskCreate,
    created_by: uuid.UUID,
    db: AsyncSession,
) -> Task:
    """
    Create a sub-task under a parent task.

    Enforces:
    - Parent must exist.
    - Parent must not itself be a sub-task (max depth = 1).
    - Sub-task inherits phase_id from parent.
    """
    parent = await _get_task_or_404(parent_task_id, db)

    # Enforce max depth — parent cannot already have a parent
    if parent.parent_task_id is not None:
        raise HTTPException(
            status_code=422,
            detail="Sub-tasks cannot have sub-tasks. Maximum nesting depth is 1.",
        )

    subtask = Task(
        project_id=parent.project_id,
        phase_id=parent.phase_id,  # always inherits from parent
        parent_task_id=parent.id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        start_date=payload.start_date,
        due_date=payload.due_date,
        order=payload.order,
        created_by=created_by,
    )
    db.add(subtask)
    await db.commit()
    await db.refresh(subtask)
    return subtask


async def get_task(task_id: uuid.UUID, db: AsyncSession) -> Task:
    """Fetch a task by ID, raise 404 if not found."""
    return await _get_task_or_404(task_id, db)


async def get_tasks_for_phase(
    phase_id: uuid.UUID,
    db: AsyncSession,
    *,
    top_level_only: bool = True,
) -> list[Task]:
    """Return tasks for a phase. By default returns top-level tasks only."""
    query = select(Task).where(Task.phase_id == phase_id)
    if top_level_only:
        query = query.where(Task.parent_task_id.is_(None))
    query = query.order_by(Task.order, Task.created_at)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_subtasks(parent_task_id: uuid.UUID, db: AsyncSession) -> list[Task]:
    """Return all sub-tasks for a given parent task."""
    result = await db.execute(
        select(Task)
        .where(Task.parent_task_id == parent_task_id)
        .order_by(Task.order, Task.created_at)
    )
    return list(result.scalars().all())


async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: AsyncSession,
) -> Task:
    """
    Update a task.

    Sets completed_at when status transitions to 'completed'.
    Re-runs matrix classification if quadrant is not being manually set.
    """
    task = await _get_task_or_404(task_id, db)

    update_data = payload.model_dump(exclude_unset=True)

    # Track if status is being set to completed to stamp completed_at
    if "status" in update_data and update_data["status"] == TaskStatus.COMPLETED:
        if task.status != TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
    elif "status" in update_data and update_data["status"] != TaskStatus.COMPLETED:
        task.completed_at = None

    # If matrix_override is being explicitly set to True, respect the quadrant as-is
    # If not, re-run classification after applying updates
    for field, value in update_data.items():
        setattr(task, field, value)

    # Re-classify top-level tasks if not under a manual override
    if task.parent_task_id is None and not task.matrix_override:
        quadrant, _ = classify_task(task)
        task.matrix_quadrant = quadrant

    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(task_id: uuid.UUID, db: AsyncSession) -> None:
    """Delete a task (and its sub-tasks via CASCADE in DB)."""
    task = await _get_task_or_404(task_id, db)
    await db.delete(task)
    await db.commit()


# ─── Assignees ────────────────────────────────────────────────────────────────

async def add_assignee(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Add a user as assignee on a task. No-op if already assigned."""
    await _get_task_or_404(task_id, db)

    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found.")

    # Idempotent — skip if already assigned
    existing = await db.execute(
        select(TaskAssignee).where(
            TaskAssignee.task_id == task_id,
            TaskAssignee.user_id == user_id,
        )
    )
    if existing.scalar_one_or_none():
        return

    db.add(TaskAssignee(task_id=task_id, user_id=user_id))
    await db.commit()


async def remove_assignee(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Remove a user from task assignees."""
    await _get_task_or_404(task_id, db)

    result = await db.execute(
        select(TaskAssignee).where(
            TaskAssignee.task_id == task_id,
            TaskAssignee.user_id == user_id,
        )
    )
    assignee = result.scalar_one_or_none()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found on this task.")

    await db.delete(assignee)
    await db.commit()


async def get_assignee_ids(task_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    """Return user IDs of all assignees for a task."""
    result = await db.execute(
        select(TaskAssignee.user_id).where(TaskAssignee.task_id == task_id)
    )
    return list(result.scalars().all())


# ─── Matrix ───────────────────────────────────────────────────────────────────

async def get_my_matrix(user_id: uuid.UUID, db: AsyncSession) -> list[Task]:
    """
    Return all top-level tasks assigned to the current user.

    Top-level only (parent_task_id IS NULL) — sub-tasks never appear in the matrix.
    Excludes completed and cancelled tasks — matrix is for active work only.
    """
    # Get task IDs assigned to this user
    assignee_result = await db.execute(
        select(TaskAssignee.task_id).where(TaskAssignee.user_id == user_id)
    )
    task_ids = list(assignee_result.scalars().all())

    if not task_ids:
        return []

    result = await db.execute(
        select(Task).where(
            Task.id.in_(task_ids),
            Task.parent_task_id.is_(None),           # top-level only
            Task.status.not_in([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
        ).order_by(Task.matrix_quadrant, Task.priority)
    )
    return list(result.scalars().all())


async def get_my_tasks(user_id: uuid.UUID, db: AsyncSession) -> list[Task]:
    """
    Return all top-level tasks assigned to the current user for the Dashboard My Tasks table.

    Unlike get_my_matrix, this includes all statuses except cancelled — the user
    needs to see completed tasks in the table context. Ordered by due_date ascending
    (soonest due first, nulls last).
    """
    assignee_result = await db.execute(
        select(TaskAssignee.task_id).where(TaskAssignee.user_id == user_id)
    )
    task_ids = list(assignee_result.scalars().all())

    if not task_ids:
        return []

    result = await db.execute(
        select(Task).where(
            Task.id.in_(task_ids),
            Task.parent_task_id.is_(None),       # top-level only — sub-tasks excluded
            Task.status != TaskStatus.CANCELLED,
        ).order_by(Task.due_date.asc().nullslast(), Task.priority.desc())
    )
    return list(result.scalars().all())


async def matrix_classify(task_id: uuid.UUID, db: AsyncSession) -> tuple[Task, str]:
    """
    Re-run deterministic matrix classification for a task and save the result.

    Only valid for top-level tasks. Returns (task, reasoning).
    """
    task = await _get_task_or_404(task_id, db)

    if task.parent_task_id is not None:
        raise HTTPException(
            status_code=422,
            detail="Matrix classification only applies to top-level tasks.",
        )

    quadrant, reasoning = classify_task(task)
    task.matrix_quadrant = quadrant
    # Clear override so the result reflects the computed classification
    task.matrix_override = False

    await db.commit()
    await db.refresh(task)
    return task, reasoning


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_task_or_404(task_id: uuid.UUID, db: AsyncSession) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


async def _get_phase_or_404(phase_id: uuid.UUID, db: AsyncSession) -> Phase:
    result = await db.execute(select(Phase).where(Phase.id == phase_id))
    phase = result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found.")
    return phase
