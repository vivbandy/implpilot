"""Tasks router — task CRUD, sub-tasks, assignees, and Eisenhower matrix."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.task import (
    MatrixClassifyRequest,
    MatrixClassifyResponse,
    SubTaskCreate,
    TaskOut,
    TaskUpdate,
)
from app.services import task_service
from app.utils.dependencies import get_current_user

router = APIRouter()


# ─── Task detail, update, delete ──────────────────────────────────────────────

@router.get("/my-matrix", response_model=list[TaskOut])
async def get_my_matrix(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskOut]:
    """
    Return top-level tasks assigned to the current user for the Eisenhower matrix.

    Excludes completed and cancelled tasks.
    Sub-tasks never appear here — matrix is top-level only.

    NOTE: This route must be declared before /{task_id} to prevent FastAPI
    from matching 'my-matrix' as a UUID path parameter.
    """
    tasks = await task_service.get_my_matrix(current_user.id, db)
    return [await _task_to_out(t, db) for t in tasks]


@router.post("/matrix-classify", response_model=MatrixClassifyResponse)
async def matrix_classify(
    payload: MatrixClassifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MatrixClassifyResponse:
    """
    Re-run deterministic Eisenhower classification for a top-level task.

    Clears any manual override and recomputes the quadrant.
    """
    task, reasoning = await task_service.matrix_classify(payload.task_id, db)
    return MatrixClassifyResponse(
        task_id=task.id,
        quadrant=task.matrix_quadrant,
        reasoning=reasoning,
    )


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    """Return task detail including sub_tasks and assignee_ids."""
    task = await task_service.get_task(task_id, db)
    return await _task_to_out(task, db)


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    """Update a task. Automatically re-classifies matrix quadrant unless overridden."""
    task = await task_service.update_task(task_id, payload, db)
    return await _task_to_out(task, db)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a task. Sub-tasks are deleted via CASCADE."""
    await task_service.delete_task(task_id, db)


# ─── Sub-tasks ────────────────────────────────────────────────────────────────

@router.post("/{task_id}/subtasks", response_model=TaskOut, status_code=201)
async def create_subtask(
    task_id: uuid.UUID,
    payload: SubTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    """
    Create a sub-task under a top-level task.

    Enforces max depth 1 — rejects with 422 if parent is already a sub-task.
    Sub-task inherits phase_id from parent.
    """
    subtask = await task_service.create_subtask(
        parent_task_id=task_id,
        payload=payload,
        created_by=current_user.id,
        db=db,
    )
    return await _task_to_out(subtask, db)


@router.get("/{task_id}/subtasks", response_model=list[TaskOut])
async def list_subtasks(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskOut]:
    """List all sub-tasks for a given task."""
    # Verify parent exists first
    await task_service.get_task(task_id, db)
    subtasks = await task_service.get_subtasks(task_id, db)
    return [await _task_to_out(t, db) for t in subtasks]


# ─── Assignees ────────────────────────────────────────────────────────────────

@router.post("/{task_id}/assignees", status_code=204)
async def add_assignee(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Add a user as assignee. Idempotent — no error if already assigned."""
    await task_service.add_assignee(task_id, user_id, db)


@router.delete("/{task_id}/assignees/{user_id}", status_code=204)
async def remove_assignee(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a user from task assignees."""
    await task_service.remove_assignee(task_id, user_id, db)


# ─── Helper ───────────────────────────────────────────────────────────────────

async def _task_to_out(task, db: AsyncSession) -> TaskOut:
    """
    Build a TaskOut with assignee_ids and sub_tasks populated.

    sub_tasks are only loaded for top-level tasks — sub-tasks don't have sub-tasks.
    """
    assignee_ids = await task_service.get_assignee_ids(task.id, db)

    sub_tasks: list[TaskOut] = []
    if task.parent_task_id is None:
        children = await task_service.get_subtasks(task.id, db)
        for child in children:
            child_assignee_ids = await task_service.get_assignee_ids(child.id, db)
            sub_tasks.append(TaskOut(
                **{c: getattr(child, c) for c in TaskOut.model_fields
                   if c not in ("assignee_ids", "sub_tasks") and hasattr(child, c)},
                assignee_ids=child_assignee_ids,
                sub_tasks=[],
            ))

    return TaskOut(
        **{c: getattr(task, c) for c in TaskOut.model_fields
           if c not in ("assignee_ids", "sub_tasks") and hasattr(task, c)},
        assignee_ids=assignee_ids,
        sub_tasks=sub_tasks,
    )
