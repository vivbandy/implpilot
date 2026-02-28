"""Project model."""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProjectStatus(str, enum.Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    AT_RISK = "at_risk"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CurrentPhase(str, enum.Enum):
    """Current phase enumeration (denormalized field)."""
    KICKOFF = "kickoff"
    DESIGN = "design"
    IMPLEMENT = "implement"
    DEPLOY = "deploy"


class Project(Base):
    """
    Project model.

    Represents a customer implementation project.
    Health score is computed and updated by health_calculator.py.
    current_phase is denormalized for fast display; updated when a phase becomes active.
    """
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    customer_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus),
        default=ProjectStatus.ACTIVE,
        nullable=False,
    )
    health_score: Mapped[int | None] = mapped_column(Integer)  # 0-100, computed
    current_phase: Mapped[CurrentPhase] = mapped_column(
        Enum(CurrentPhase),
        default=CurrentPhase.KICKOFF,
        nullable=False,
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    target_end_date: Mapped[date | None] = mapped_column(Date)
    actual_end_date: Mapped[date | None] = mapped_column(Date)

    # Foreign keys
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, customer={self.customer_name})>"
