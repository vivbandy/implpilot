"""Related object models: Notes, Attachments, External Tickets, Feature Requests, Escalations, Contacts."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ─── Notes ───────────────────────────────────────────────────────────────────

class NoteEntityType(str, enum.Enum):
    """Entity types that can have notes."""
    PROJECT = "project"
    PHASE = "phase"
    TASK = "task"
    FEATURE_REQUEST = "feature_request"
    ESCALATION = "escalation"


class Note(Base):
    """
    Note model.

    Polymorphic notes that can attach to projects, phases, tasks,
    feature requests, or escalations.
    """
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    entity_type: Mapped[NoteEntityType] = mapped_column(
        Enum(NoteEntityType),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Note(id={self.id}, entity_type={self.entity_type}, entity_id={self.entity_id})>"


# ─── Attachments ─────────────────────────────────────────────────────────────

class AttachmentEntityType(str, enum.Enum):
    """Entity types that can have attachments."""
    PROJECT = "project"
    PHASE = "phase"
    TASK = "task"
    FEATURE_REQUEST = "feature_request"
    ESCALATION = "escalation"


class Attachment(Base):
    """
    Attachment model.

    Polymorphic attachments (links to external files/docs).
    MVP stores URL only; file upload (S3) is out of scope.
    """
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    entity_type: Mapped[AttachmentEntityType] = mapped_column(
        Enum(AttachmentEntityType),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Attachment(id={self.id}, label={self.label}, entity_type={self.entity_type})>"


# ─── External Tickets ────────────────────────────────────────────────────────

class ExternalTicketEntityType(str, enum.Enum):
    """Entity types that can have external tickets."""
    TASK = "task"
    FEATURE_REQUEST = "feature_request"
    ESCALATION = "escalation"


class ExternalTicketSystem(str, enum.Enum):
    """External ticket system enumeration."""
    JIRA = "jira"
    ZENDESK = "zendesk"
    OTHER = "other"


class ExternalTicket(Base):
    """
    External ticket model.

    Links tasks/feature requests/escalations to external systems (Jira, Zendesk).
    MVP: URL-only, no live sync. status_cache is manually updated.
    Future: live sync with external APIs.
    """
    __tablename__ = "external_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    entity_type: Mapped[ExternalTicketEntityType] = mapped_column(
        Enum(ExternalTicketEntityType),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    ticket_system: Mapped[ExternalTicketSystem] = mapped_column(
        Enum(ExternalTicketSystem),
        nullable=False,
    )
    ticket_id: Mapped[str | None] = mapped_column(String)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str | None] = mapped_column(String)
    status_cache: Mapped[str | None] = mapped_column(String)
    last_synced_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<ExternalTicket(id={self.id}, system={self.ticket_system}, entity_type={self.entity_type})>"


# ─── Feature Requests ────────────────────────────────────────────────────────

class FeatureRequestPriority(str, enum.Enum):
    """Feature request priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeatureRequestStatus(str, enum.Enum):
    """Feature request status enumeration."""
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    PLANNED = "planned"
    SHIPPED = "shipped"
    DECLINED = "declined"


class FeatureRequestSource(str, enum.Enum):
    """Feature request source enumeration."""
    MANUAL = "manual"
    TAG_DERIVED = "tag_derived"


class FeatureRequest(Base):
    """
    Feature request model.

    Can be created manually or auto-generated from tags.
    Optionally linked to a task or phase.
    """
    __tablename__ = "feature_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("phases.id", ondelete="SET NULL"),
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    why_important: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[FeatureRequestPriority] = mapped_column(
        Enum(FeatureRequestPriority),
        default=FeatureRequestPriority.MEDIUM,
        nullable=False,
    )
    status: Mapped[FeatureRequestStatus] = mapped_column(
        Enum(FeatureRequestStatus),
        default=FeatureRequestStatus.OPEN,
        nullable=False,
    )
    requested_by: Mapped[str | None] = mapped_column(String)
    source: Mapped[FeatureRequestSource] = mapped_column(
        Enum(FeatureRequestSource),
        default=FeatureRequestSource.MANUAL,
        nullable=False,
    )
    source_note_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("notes.id", ondelete="SET NULL"),
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<FeatureRequest(id={self.id}, title={self.title}, status={self.status})>"


# ─── Escalations ─────────────────────────────────────────────────────────────

class EscalationSeverity(str, enum.Enum):
    """Escalation severity enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationStatus(str, enum.Enum):
    """Escalation status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EscalationSource(str, enum.Enum):
    """Escalation source enumeration."""
    MANUAL = "manual"
    TAG_DERIVED = "tag_derived"


class Escalation(Base):
    """
    Escalation model.

    Can be created manually or auto-generated from tags.
    Optionally linked to a task or phase.
    """
    __tablename__ = "escalations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("phases.id", ondelete="SET NULL"),
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[EscalationSeverity] = mapped_column(
        Enum(EscalationSeverity),
        default=EscalationSeverity.MEDIUM,
        nullable=False,
    )
    status: Mapped[EscalationStatus] = mapped_column(
        Enum(EscalationStatus),
        default=EscalationStatus.OPEN,
        nullable=False,
    )
    raised_by: Mapped[str | None] = mapped_column(String)
    source: Mapped[EscalationSource] = mapped_column(
        Enum(EscalationSource),
        default=EscalationSource.MANUAL,
        nullable=False,
    )
    source_note_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("notes.id", ondelete="SET NULL"),
    )
    resolved_at: Mapped[datetime | None] = mapped_column()
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Escalation(id={self.id}, title={self.title}, severity={self.severity})>"


# ─── Contacts ────────────────────────────────────────────────────────────────

class Contact(Base):
    """
    Contact model.

    Customer contacts for a project (stakeholders, decision makers, etc.).
    """
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String)
    role: Mapped[str | None] = mapped_column(String)
    company: Mapped[str | None] = mapped_column(String)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, name={self.name}, project_id={self.project_id})>"
