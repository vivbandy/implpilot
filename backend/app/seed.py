"""Seed script for initial data: admin user + built-in tag definitions."""
import asyncio
import sys

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.tag import TagDefinition, TagCategory, TagSentiment, TagAutoAction


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Built-in tag definitions as specified in Section 3.12 of the spec
BUILT_IN_TAGS = [
    {
        "name": "escalated",
        "category": TagCategory.ESCALATION,
        "sentiment": TagSentiment.NEGATIVE,
        "auto_action": TagAutoAction.CREATE_ESCALATION,
        "description": "Issue has been escalated",
        "color": "#E2445C",
    },
    {
        "name": "blockedbycustomer",
        "category": TagCategory.ESCALATION,
        "sentiment": TagSentiment.NEGATIVE,
        "auto_action": TagAutoAction.CREATE_ESCALATION,
        "description": "Blocked by customer action/decision",
        "color": "#E2445C",
    },
    {
        "name": "atrisk",
        "category": TagCategory.ESCALATION,
        "sentiment": TagSentiment.NEGATIVE,
        "auto_action": TagAutoAction.CREATE_ESCALATION,
        "description": "Project or task is at risk",
        "color": "#E2445C",
    },
    {
        "name": "customerenhancement",
        "category": TagCategory.FEATURE_REQUEST,
        "sentiment": TagSentiment.NEUTRAL,
        "auto_action": TagAutoAction.CREATE_FEATURE_REQUEST,
        "description": "Customer requested enhancement",
        "color": "#0073EA",
    },
    {
        "name": "featurerequest",
        "category": TagCategory.FEATURE_REQUEST,
        "sentiment": TagSentiment.NEUTRAL,
        "auto_action": TagAutoAction.CREATE_FEATURE_REQUEST,
        "description": "Feature request identified",
        "color": "#0073EA",
    },
    {
        "name": "productsignal",
        "category": TagCategory.FEATURE_REQUEST,
        "sentiment": TagSentiment.NEUTRAL,
        "auto_action": TagAutoAction.CREATE_FEATURE_REQUEST,
        "description": "Signal for product team",
        "color": "#0073EA",
    },
    {
        "name": "customerhappy",
        "category": TagCategory.SENTIMENT,
        "sentiment": TagSentiment.POSITIVE,
        "auto_action": TagAutoAction.NONE,
        "description": "Customer expressed satisfaction",
        "color": "#00C875",
    },
    {
        "name": "goodprogress",
        "category": TagCategory.SENTIMENT,
        "sentiment": TagSentiment.POSITIVE,
        "auto_action": TagAutoAction.NONE,
        "description": "Good progress noted",
        "color": "#00C875",
    },
    {
        "name": "frustrated",
        "category": TagCategory.SENTIMENT,
        "sentiment": TagSentiment.NEGATIVE,
        "auto_action": TagAutoAction.NONE,
        "description": "Customer frustration detected",
        "color": "#FDAB3D",
    },
    {
        "name": "churnrisk",
        "category": TagCategory.SENTIMENT,
        "sentiment": TagSentiment.NEGATIVE,
        "auto_action": TagAutoAction.NONE,
        "description": "Risk of customer churn",
        "color": "#E2445C",
    },
    {
        "name": "slowadoption",
        "category": TagCategory.SENTIMENT,
        "sentiment": TagSentiment.NEGATIVE,
        "auto_action": TagAutoAction.NONE,
        "description": "Slow user adoption",
        "color": "#FDAB3D",
    },
]


async def seed_admin_user(db: AsyncSession) -> None:
    """Create default admin user if it doesn't exist."""
    # Check if admin user already exists
    result = await db.execute(
        select(User).where(User.email == "admin@example.com")
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        print("✓ Admin user already exists")
        return

    # Create admin user
    admin_user = User(
        email="admin@example.com",
        username="admin",
        password_hash=pwd_context.hash("admin123"),  # Change this in production!
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
    )

    db.add(admin_user)
    await db.commit()
    print("✓ Created admin user (email: admin@example.com, password: admin123)")


async def seed_tag_definitions(db: AsyncSession) -> None:
    """Create built-in tag definitions if they don't exist."""
    created_count = 0

    for tag_data in BUILT_IN_TAGS:
        # Check if tag already exists
        result = await db.execute(
            select(TagDefinition).where(TagDefinition.name == tag_data["name"])
        )
        existing_tag = result.scalar_one_or_none()

        if existing_tag:
            continue

        # Create tag definition
        tag = TagDefinition(**tag_data)
        db.add(tag)
        created_count += 1

    await db.commit()

    if created_count > 0:
        print(f"✓ Created {created_count} tag definitions")
    else:
        print("✓ Tag definitions already exist")


async def main() -> None:
    """Run all seed operations."""
    print("Starting seed script...")

    async with AsyncSessionLocal() as db:
        try:
            await seed_admin_user(db)
            await seed_tag_definitions(db)
            print("\n✅ Seed script completed successfully!")
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}", file=sys.stderr)
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
