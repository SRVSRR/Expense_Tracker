"""Categorization routes — suggest categories, log corrections, train ML model."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db
from app.models import CorrectionLog, User
from app.services.categorize import get_all_categories
from app.ml.categorizer import get_categorizer
from app.utils import generate_uuid, get_current_user

router = APIRouter()


class SuggestRequest(BaseModel):
    description: str
    merchant: Optional[str] = None


class SuggestResponse(BaseModel):
    suggested_category: Optional[str]
    confidence: str  # "high", "medium", "low", "none"
    all_categories: list[str]
    source: str  # "ml", "rules", "none"


class CorrectionRequest(BaseModel):
    description: str
    merchant: Optional[str] = None
    suggested_category: str
    corrected_category: str


class TrainResponse(BaseModel):
    status: str
    samples: int
    accuracy: Optional[float] = None
    num_classes: Optional[int] = None
    required: Optional[int] = None


@router.post("/suggest", response_model=SuggestResponse)
async def categorize_suggest(
    data: SuggestRequest,
    current_user: User = Depends(get_current_user),
):
    """Suggest a category using ML model with rule-based fallback."""
    cat = get_categorizer()
    category, confidence, prob = cat.predict(data.description, data.merchant)

    source = "none"
    if category:
        source = "ml" if (cat.is_trained and prob > 0) else "rules"

    return SuggestResponse(
        suggested_category=category,
        confidence=confidence,
        all_categories=get_all_categories(),
        source=source,
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


@router.post("/train", response_model=TrainResponse)
async def train_model(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Train the ML categorization model on all logged corrections.

    Uses data from ALL users (corrections improve for everyone).
    Requires minimum 30 samples.
    """
    result = await db.execute(select(CorrectionLog))
    logs = result.scalars().all()

    if not logs:
        return TrainResponse(status="no_data", samples=0, required=30)

    texts = []
    labels = []
    for log in logs:
        text_parts = [log.description or ""]
        if log.merchant:
            text_parts.append(log.merchant)
        texts.append(" ".join(text_parts))
        labels.append(log.corrected_category)

    cat = get_categorizer()
    stats = cat.train(texts, labels)

    return TrainResponse(
        status=stats["status"],
        samples=stats["samples"],
        accuracy=stats.get("accuracy"),
        num_classes=stats.get("num_classes"),
        required=stats.get("required"),
    )


@router.get("/model-info")
async def model_info(
    current_user: User = Depends(get_current_user),
):
    """Get info about the current ML model."""
    cat = get_categorizer()
    return {
        "is_trained": cat.is_trained,
        "training_samples": cat.training_samples,
        "model_exists": cat.model is not None,
    }
