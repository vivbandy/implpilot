"""Report models: HealthReport and SavedView."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReportType(str, enum.Enum):
    """Report type enumeration."""
    PROJECT_HEALTH = "project_health"
    AGGREGATE = "aggregate"
    NL_QUERY = "nl_query"


class HealthReport(Base):
    """
    Health report model.

    Stores AI-generated reports with block-based structure.
    blocks_json contains the editable blocks (ai_text, chart, phase_progress, etc.).
    report_data_json contains the raw data used to generate the report.
    filters_json contains the filters/parameters used (for aggregate reports).
    """
    __tablename__ = "health_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
    )
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType),
        default=ReportType.PROJECT_HEALTH,
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    generated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    health_score: Mapped[int | None] = mapped_column(Integer)  # 0-100
    blocks_json: Mapped[dict | None] = mapped_column(JSON)
    report_data_json: Mapped[dict | None] = mapped_column(JSON)
    filters_json: Mapped[dict | None] = mapped_column(JSON)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<HealthReport(id={self.id}, type={self.report_type}, health_score={self.health_score})>"


class SavedView(Base):
    """
    Saved view model.

    Stores user-saved filter sets for projects, tasks, reports, etc.
    """
    __tablename__ = "saved_views"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    page: Mapped[str | None] = mapped_column(String)
    filters: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<SavedView(id={self.id}, name={self.name}, user_id={self.user_id})>"
