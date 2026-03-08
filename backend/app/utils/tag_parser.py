"""
Tag parser utility.

Extracts #hashtag tokens from text and matches them against known tag definitions.

Design:
- Tags in ImplPilot are written as #tagname (lowercase, no spaces, alphanumeric).
- We extract all #tokens, normalize to lowercase, and look them up in tag_definitions.
- Unknown tags are silently ignored — only recognized tag definitions produce TagEvents.
- Case-insensitive match: #Escalated and #escalated both resolve to the 'escalated' tag.
"""
import re
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import TagDefinition


# Matches #word where word is 1+ alphanumeric or underscore chars.
# We anchor to word boundary (or start) to avoid matching #tag within longer strings.
_TAG_PATTERN = re.compile(r"(?<!\w)#([a-zA-Z][a-zA-Z0-9_]*)")


@dataclass
class ParsedTag:
    """A raw tag token extracted from text before DB lookup."""
    raw: str       # the original token as written, e.g. "#Escalated"
    name: str      # normalized lowercase name, e.g. "escalated"


def extract_raw_tags(text: str) -> list[ParsedTag]:
    """
    Extract all #tag tokens from text.

    Returns a list of ParsedTag objects (raw + normalized name).
    Duplicates are kept — dedup happens in process_tags if needed.

    Example:
        extract_raw_tags("Project is #escalated and #churnrisk")
        → [ParsedTag(raw="#escalated", name="escalated"),
           ParsedTag(raw="#churnrisk", name="churnrisk")]
    """
    matches = _TAG_PATTERN.findall(text)
    return [ParsedTag(raw=f"#{m}", name=m.lower()) for m in matches]


async def resolve_tags(
    text: str,
    db: AsyncSession,
) -> list[TagDefinition]:
    """
    Extract tags from text and resolve them against the database.

    Returns only TagDefinition objects that match extracted tokens.
    Unknown tags are dropped silently.

    This is the primary entry point used by tag_service.process_tags().
    """
    parsed = extract_raw_tags(text)
    if not parsed:
        return []

    names = list({p.name for p in parsed})  # deduplicate before DB query

    result = await db.execute(
        select(TagDefinition).where(TagDefinition.name.in_(names))
    )
    return list(result.scalars().all())
