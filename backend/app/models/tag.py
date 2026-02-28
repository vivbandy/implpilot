"""Tag models: TagDefinition and TagEvent."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TagCategory(str, enum.Enum):
    """Tag category enumeration."""
    ESCALATION = "escalation"
    FEATURE_REQUEST = "feature_request"
    SENTIMENT = "sentiment"
    CUSTOM = "custom"


class TagSentiment(str, enum.Enum):
    """Tag sentiment enumeration."""
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"


class TagAutoAction(str, enum.Enum):
    """Tag auto-action enumeration."""
    CREATE_ESCALATION = "create_escalation"
    CREATE_FEATURE_REQUEST = "create_feature_request"
    NONE = "none"


class TagDefinition(Base):
    """
    Tag definition model.

    Defines available tags, their category, sentiment, and auto-actions.
    Built-in tags are seeded on first run.
    Admins can add custom tags via Settings.
    """
    __tablename__ = "tag_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    category: Mapped[TagCategory] = mapped_column(
        Enum(TagCategory),
        nullable=False,
    )
    sentiment: Mapped[TagSentiment | None] = mapped_column(Enum(TagSentiment))
    auto_action: Mapped[TagAutoAction] = mapped_column(
        Enum(TagAutoAction),
        default=TagAutoAction.NONE,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String)
    color: Mapped[str | None] = mapped_column(String)  # hex color for TagChip
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<TagDefinition(id={self.id}, name={self.name}, category={self.category})>"


class TagEntityType(str, enum.Enum):
    """Entity types that can have tags."""
    NOTE = "note"
    TASK = "task"
    EXTERNAL_TICKET = "external_ticket"


class TagEvent(Base):
    """
    Tag event model.

    Records each instance of a tag being used.
    Links tag to the entity it was found in.
    derived_id points to auto-created escalation/feature_request if auto_action fired.
    """
    __tablename__ = "tag_events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tag_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[TagEntityType] = mapped_column(
        Enum(TagEntityType),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    derived_id: Mapped[uuid.UUID | None] = mapped_column()  # FK to escalation/feature_request
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<TagEvent(id={self.id}, tag_id={self.tag_id}, entity_type={self.entity_type})>"
