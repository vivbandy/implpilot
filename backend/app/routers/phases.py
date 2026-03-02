"""Phase endpoints: list, detail, update, complete."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.phase import PhaseResponse, PhaseUpdate, PhaseWithTaskCounts
from app.services import phase_service
from app.utils.dependencies import get_current_user


router = APIRouter()


@router.get("/projects/{project_id}/phases", response_model=list[PhaseWithTaskCounts])
async def get_project_phases(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get all phases for a project with task counts.

    Returns phases ordered by order field (1-4).

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        List of phases with task statistics
    """
    phases = await phase_service.get_project_phases(db, project_id)

    phases_with_counts = []
    for phase in phases:
        counts = await phase_service.get_phase_task_counts(db, phase.id)
        phase_dict = {
            **phase.__dict__,
            **counts,
        }
        phases_with_counts.append(PhaseWithTaskCounts(**phase_dict))

    return phases_with_counts


@router.get("/{phase_id}", response_model=PhaseResponse)
async def get_phase(
    phase_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get phase detail by ID.

    Args:
        phase_id: Phase UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Phase details

    Raises:
        HTTPException: 404 if phase not found
    """
    phase = await phase_service.get_phase(db, phase_id)
    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phase not found",
        )
    return phase


@router.put("/{phase_id}", response_model=PhaseResponse)
async def update_phase(
    phase_id: UUID,
    phase_data: PhaseUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Update a phase's dates or description.

    Note: To change phase status, use the /complete endpoint.

    Args:
        phase_id: Phase UUID
        phase_data: Phase update data
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated phase

    Raises:
        HTTPException: 404 if phase not found
    """
    phase = await phase_service.update_phase(db, phase_id, phase_data)
    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phase not found",
        )
    return phase


@router.post("/{phase_id}/complete", response_model=PhaseResponse)
async def complete_phase(
    phase_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Mark a phase as completed and activate the next phase.

    This endpoint:
    1. Marks the specified phase as completed with timestamp
    2. Activates the next phase (by order)
    3. Updates projects.current_phase
    4. (Future) Fires phase_completed notification

    Args:
        phase_id: Phase UUID to complete
        current_user: Authenticated user
        db: Database session

    Returns:
        Completed phase

    Raises:
        HTTPException: 404 if phase not found
    """
    phase = await phase_service.complete_phase(db, phase_id)
    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phase not found",
        )
    return phase
