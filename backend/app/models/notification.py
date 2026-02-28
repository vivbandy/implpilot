"""Notification model."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotificationType(str, enum.Enum):
    """Notification type enumeration."""
    TASK_DUE_SOON = "task_due_soon"
    TASK_OVERDUE = "task_overdue"
    PROJECT_INACTIVE = "project_inactive"
    PHASE_COMPLETED = "phase_completed"
    ESCALATION_OPENED = "escalation_opened"
    TAG_ESCALATION_DETECTED = "tag_escalation_detected"
    MENTION = "mention"
    REPORT_READY = "report_ready"


class Notification(Base):
    """
    Notification model.

    In-app notifications with optional email delivery.
    Created by scheduled jobs, tag auto-actions, and manual triggers.
    """
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String)
    message: Mapped[str | None] = mapped_column(Text)
    entity_type: Mapped[str | None] = mapped_column(String)
    entity_id: Mapped[uuid.UUID | None] = mapped_column()
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.type}, user_id={self.user_id})>"
