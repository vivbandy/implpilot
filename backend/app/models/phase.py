"""Phase model."""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PhaseName(str, enum.Enum):
    """Phase name enumeration."""
    KICKOFF = "kickoff"
    DESIGN = "design"
    IMPLEMENT = "implement"
    DEPLOY = "deploy"


class PhaseStatus(str, enum.Enum):
    """Phase status enumeration."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


class Phase(Base):
    """
    Phase model.

    Represents one of four fixed phases in a project.
    All four phases are created automatically when a project is created.
    Only one phase should be active at a time per project.

    Phase rules (enforced in phase_service.py):
    - Phases cannot be deleted, only status/dates updated
    - Completing a phase auto-sets the next one to active
    - projects.current_phase is updated when a phase transitions to active
    """
    __tablename__ = "phases"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[PhaseName] = mapped_column(
        Enum(PhaseName),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, 4
    status: Mapped[PhaseStatus] = mapped_column(
        Enum(PhaseStatus),
        default=PhaseStatus.PENDING,
        nullable=False,
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    target_end_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column()
    description: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_project_phase_name"),
    )

    def __repr__(self) -> str:
        return f"<Phase(id={self.id}, project_id={self.project_id}, name={self.name}, status={self.status})>"
