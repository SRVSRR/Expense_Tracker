"""Categorization routes — suggest categories and log corrections."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db
from app.models import CorrectionLog, User
from app.services.categorize import suggest_category, get_all_categories, KEYWORD_MAP
from app.utils import generate_uuid, get_current_user

router = APIRouter()


class SuggestRequest(BaseModel):
    description: str
    merchant: Optional[str] = None


class SuggestResponse(BaseModel):
    suggested_category: Optional[str]
    confidence: str  # "high", "medium", "low", "none"
    all_categories: list[str]


class CorrectionRequest(BaseModel):
    description: str
    merchant: Optional[str] = None
    suggested_category: str
    corrected_category: str


@router.post("/suggest", response_model=SuggestResponse)
async def categorize_suggest(
    data: SuggestRequest,
    current_user: User = Depends(get_current_user),
):
    """Suggest a category for a transaction based on description/merchant keywords."""
    suggested = suggest_category(data.description, data.merchant)

    # Determine confidence based on match specificity
    confidence = "none"
    if suggested:
        text = f"{data.description} {data.merchant or ''}".lower()
        keywords = KEYWORD_MAP.get(suggested, [])
        max_match_len = max((len(kw) for kw in keywords if kw in text), default=0)
        if max_match_len >= 8:
            confidence = "high"
        elif max_match_len >= 4:
            confidence = "medium"
        else:
            confidence = "low"

    return SuggestResponse(
        suggested_category=suggested,
        confidence=confidence,
        all_categories=get_all_categories(),
    )


@router.post("/corrections")
async def log_correction(
    data: CorrectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log when a user overrides a suggested category. Used for future ML training."""
    log = CorrectionLog(
        id=generate_uuid(),
        user_id=current_user.id,
        description=data.description,
        merchant=data.merchant,
        suggested_category=data.suggested_category,
        corrected_category=data.corrected_category,
    )
    db.add(log)
    await db.commit()
    return {"status": "logged"}
