"""Tasks router — task CRUD, sub-tasks, assignees, and Eisenhower matrix."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import (
    MatrixClassifyRequest,
    MatrixClassifyResponse,
    SubTaskCreate,
    SubTaskResponse,
    TaskResponse,
    TaskUpdate,
)
from app.services import task_service
from app.utils.dependencies import get_current_user

router = APIRouter()


# ─── Matrix ───────────────────────────────────────────────────────────────────

@router.get("/my-matrix", response_model=list[TaskResponse])
async def get_my_matrix(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    """
    Return top-level tasks assigned to the current user for the Eisenhower matrix.

    Excludes completed and cancelled tasks.
    Sub-tasks never appear here — matrix is top-level only.

    NOTE: This route must be declared before /{task_id} to prevent FastAPI
    from matching 'my-matrix' as a UUID path parameter.
    """
    tasks = await task_service.get_my_matrix(current_user.id, db)
    return [await _task_to_response(t, db) for t in tasks]


@router.post("/matrix-classify", response_model=MatrixClassifyResponse)
async def matrix_classify(
    payload: MatrixClassifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MatrixClassifyResponse:
    """Re-run deterministic Eisenhower classification for a top-level task."""
    task, reasoning = await task_service.matrix_classify(payload.task_id, db)
    return MatrixClassifyResponse(
        task_id=task.id,
        quadrant=task.matrix_quadrant,
        reasoning=reasoning,
    )


# ─── Task CRUD ────────────────────────────────────────────────────────────────

@router.get("/{task_id}", response_model=TaskResponse | SubTaskResponse)
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse | SubTaskResponse:
    """
    Return task detail.

    Returns TaskResponse (with sub_tasks) for top-level tasks.
    Returns SubTaskResponse (no sub_tasks field) for sub-tasks.
    """
    task = await task_service.get_task(task_id, db)
    if task.parent_task_id is None:
        return await _task_to_response(task, db)
    return await _subtask_to_response(task, db)


@router.put("/{task_id}", response_model=TaskResponse | SubTaskResponse)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse | SubTaskResponse:
    """Update a task. Re-classifies matrix quadrant for top-level tasks unless overridden."""
    task = await task_service.update_task(task_id, payload, db)
    if task.parent_task_id is None:
        return await _task_to_response(task, db)
    return await _subtask_to_response(task, db)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a task. Sub-tasks are deleted via CASCADE."""
    await task_service.delete_task(task_id, db)


# ─── Sub-tasks ────────────────────────────────────────────────────────────────

@router.post("/{task_id}/subtasks", response_model=SubTaskResponse, status_code=201)
async def create_subtask(
    task_id: uuid.UUID,
    payload: SubTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubTaskResponse:
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
    return await _subtask_to_response(subtask, db)


@router.get("/{task_id}/subtasks", response_model=list[SubTaskResponse])
async def list_subtasks(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SubTaskResponse]:
    """List all sub-tasks for a given task."""
    await task_service.get_task(task_id, db)  # verify parent exists
    subtasks = await task_service.get_subtasks(task_id, db)
    return [await _subtask_to_response(t, db) for t in subtasks]


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


# ─── Response builders ────────────────────────────────────────────────────────

async def _task_to_response(task: Task, db: AsyncSession) -> TaskResponse:
    """
    Build a TaskResponse for a top-level task.

    Populates assignee_ids and sub_tasks (as SubTaskResponse — no children).
    Only called for tasks where parent_task_id is None.
    """
    assignee_ids = await task_service.get_assignee_ids(task.id, db)
    children = await task_service.get_subtasks(task.id, db)
    sub_tasks = [await _subtask_to_response(c, db) for c in children]

    return TaskResponse(
        **{f: getattr(task, f) for f in TaskResponse.model_fields
           if f not in ("assignee_ids", "sub_tasks") and hasattr(task, f)},
        assignee_ids=assignee_ids,
        sub_tasks=sub_tasks,
    )


async def _subtask_to_response(task: Task, db: AsyncSession) -> SubTaskResponse:
    """
    Build a SubTaskResponse for a sub-task.

    No sub_tasks field — sub-tasks cannot have children.
    """
    assignee_ids = await task_service.get_assignee_ids(task.id, db)

    return SubTaskResponse(
        **{f: getattr(task, f) for f in SubTaskResponse.model_fields
           if f != "assignee_ids" and hasattr(task, f)},
        assignee_ids=assignee_ids,
    )
