"""Seed default categories for new users."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Category
from app.utils import generate_uuid


# (name, type, color, icon)
DEFAULT_CATEGORIES = [
    # Expense
    ("Food & Dining",       "expense", "#EF5350", "\u25AA"),
    ("Transportation",      "expense", "#42A5F5", "\u25B6"),
    ("Shopping",            "expense", "#EC407A", "\u25A1"),
    ("Bills & Utilities",   "expense", "#FFA726", "\u25A3"),
    ("Housing",             "expense", "#66BB6A", "\u2302"),
    ("Entertainment",       "expense", "#AB47BC", "\u25B8"),
    ("Health & Medical",    "expense", "#EF5350", "\u271A"),
    ("Subscriptions",       "expense", "#26C6DA", "\u21BB"),
    ("Education",           "expense", "#5C6BC0", "\u25CB"),
    ("Travel",              "expense", "#26C6DA", "\u25C6"),
    ("Personal Care",       "expense", "#EC407A", "\u2606"),
    ("Pets",                "expense", "#8D6E63", "\u2022"),
    ("Gifts & Donations",   "expense", "#EF5350", "\u2661"),
    # Income
    ("Income",              "income",  "#66BB6A", "\u25B3"),
]


async def seed_categories(user_id: str, db: AsyncSession) -> None:
    """Insert default categories for a newly registered user.

    Skips any categories that already exist for this user (idempotent).
    """
    existing = await db.execute(
        select(Category.name).where(Category.user_id == user_id)
    )
    existing_names = {row[0] for row in existing.all()}

    for name, cat_type, color, icon in DEFAULT_CATEGORIES:
        if name in existing_names:
            continue
        db.add(Category(
            id=generate_uuid(),
            user_id=user_id,
            name=name,
            type=cat_type,
            color=color,
            icon=icon,
        ))

    await db.commit()
