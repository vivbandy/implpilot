"""Project endpoints: CRUD, health, filters."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectWithPhases,
)
from app.schemas.phase import PhaseWithTaskCounts
from app.services import project_service, phase_service
from app.utils.dependencies import get_current_user
from app.utils.health_calculator import calculate_project_health


router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create a new project.

    This automatically creates 4 default phases (kickoff, design, implement, deploy).
    The first phase (kickoff) is set to active by default.

    Args:
        project_data: Project creation data
        current_user: Authenticated user
        db: Database session

    Returns:
        Created project
    """
    # Create project
    project = await project_service.create_project(
        db,
        project_data,
        created_by_id=current_user.id,
    )

    # Create default phases
    await phase_service.create_default_phases(db, project.id)

    return project


@router.get("", response_model=list[ProjectResponse])
async def get_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    owner_id: UUID | None = None,
    status: str | None = None,
):
    """
    Get list of projects with optional filters.

    Args:
        current_user: Authenticated user
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        owner_id: Filter by owner ID
        status: Filter by status

    Returns:
        List of projects
    """
    projects = await project_service.get_projects(
        db,
        skip=skip,
        limit=limit,
        owner_id=owner_id,
        status=status,
    )
    return projects


@router.get("/{project_id}", response_model=ProjectWithPhases)
async def get_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get a project by ID with phases array including task counts.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Project with phases array

    Raises:
        HTTPException: 404 if project not found
    """
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get phases with task counts
    phases = await phase_service.get_project_phases(db, project_id)
    phases_with_counts = []
    for phase in phases:
        counts = await phase_service.get_phase_task_counts(db, phase.id)
        phase_dict = {
            **phase.__dict__,
            **counts,
        }
        phases_with_counts.append(PhaseWithTaskCounts(**phase_dict))

    # Build response with phases
    project_dict = project.__dict__
    project_dict["phases"] = phases_with_counts

    return ProjectWithPhases(**project_dict)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Update a project.

    Args:
        project_id: Project UUID
        project_data: Project update data
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated project

    Raises:
        HTTPException: 404 if project not found
    """
    project = await project_service.update_project(db, project_id, project_data)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Delete a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Raises:
        HTTPException: 404 if project not found
    """
    deleted = await project_service.delete_project(db, project_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )


@router.get("/{project_id}/health")
async def get_project_health(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Calculate and return project health score.

    The score is computed based on:
    - Overdue tasks
    - Critical escalations
    - Inactivity
    - Blocked tasks
    - Sentiment tags
    - Tag-derived escalations
    - Overdue phases

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Health score (0-100) and label

    Raises:
        HTTPException: 404 if project not found
    """
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Calculate health score
    health_score = await calculate_project_health(db, project_id)

    # Update project's health_score field
    await project_service.update_project_health_score(db, project_id, health_score)

    # Determine label based on score
    if health_score >= 75:
        label = "Healthy"
    elif health_score >= 60:
        label = "On Track"
    elif health_score >= 40:
        label = "Needs Attention"
    else:
        label = "At Risk"

    return {
        "project_id": project_id,
        "health_score": health_score,
        "label": label,
    }
