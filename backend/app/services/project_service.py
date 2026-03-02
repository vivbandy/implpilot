"""Project service: CRUD operations and business logic."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


async def create_project(
    db: AsyncSession,
    project_data: ProjectCreate,
    created_by_id: UUID,
) -> Project:
    """
    Create a new project.

    Note: Caller must call phase_service.create_default_phases()
    after creating the project.

    Args:
        db: Database session
        project_data: Project creation data
        created_by_id: User ID creating the project

    Returns:
        Created project model
    """
    project = Project(
        name=project_data.name,
        customer_name=project_data.customer_name,
        description=project_data.description,
        start_date=project_data.start_date,
        target_end_date=project_data.target_end_date,
        owner_id=project_data.owner_id,
        created_by=created_by_id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_project(db: AsyncSession, project_id: UUID) -> Project | None:
    """
    Get a project by ID.

    Args:
        db: Database session
        project_id: Project UUID

    Returns:
        Project model if found, None otherwise
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    return result.scalar_one_or_none()


async def get_projects(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    owner_id: UUID | None = None,
    status: str | None = None,
) -> list[Project]:
    """
    Get list of projects with optional filters.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        owner_id: Filter by owner ID
        status: Filter by status

    Returns:
        List of project models
    """
    query = select(Project)

    if owner_id:
        query = query.where(Project.owner_id == owner_id)
    if status:
        query = query.where(Project.status == status)

    query = query.offset(skip).limit(limit).order_by(Project.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_project(
    db: AsyncSession,
    project_id: UUID,
    project_data: ProjectUpdate,
) -> Project | None:
    """
    Update a project.

    Args:
        db: Database session
        project_id: Project UUID
        project_data: Project update data

    Returns:
        Updated project model if found, None otherwise
    """
    project = await get_project(db, project_id)
    if not project:
        return None

    # Update only provided fields
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project_id: UUID) -> bool:
    """
    Delete a project.

    Args:
        db: Database session
        project_id: Project UUID

    Returns:
        True if deleted, False if not found
    """
    project = await get_project(db, project_id)
    if not project:
        return False

    await db.delete(project)
    await db.commit()
    return True


async def update_project_health_score(
    db: AsyncSession,
    project_id: UUID,
    health_score: int,
) -> None:
    """
    Update a project's health score.

    This is called by health_calculator after computing the score.

    Args:
        db: Database session
        project_id: Project UUID
        health_score: Computed health score (0-100)
    """
    project = await get_project(db, project_id)
    if project:
        project.health_score = health_score
        await db.commit()
