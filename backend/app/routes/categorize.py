"""Categorization routes — suggest categories, log corrections, train ML model."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.database import get_db
from app.models import CorrectionLog
from app.services.categorize import get_all_categories
from app.ml.categorizer import get_categorizer
from app.utils import generate_uuid, get_current_user
from app.schemas import (
    CategorizeSuggestRequest,
    CategorizeSuggestResponse,
    CategorizeCorrectionRequest,
    CategorizeTrainResponse,
    CategorizeModelInfo,
)
from app.utils.rate_limit import limiter

router = APIRouter()


@router.post(
    "/suggest",
    response_model=CategorizeSuggestResponse,
    summary="Suggest transaction category",
    description="Returns a suggested category for a transaction description using ML model with rule-based fallback. Confidence levels: high (>0.8), medium (0.55-0.8), low (<0.55), none (no match).",
    responses={
        200: {"description": "Category suggestion with confidence"},
        401: {"description": "Unauthorized - invalid or missing token"},
    },
)
async def categorize_suggest(
    data: CategorizeSuggestRequest,
    current_user = Depends(get_current_user),
):
    """Suggest a category using ML model with rule-based fallback."""
    cat = get_categorizer()
    category, confidence, prob = cat.predict(data.description, data.merchant)

    source = "none"
    if category:
        source = "ml" if (cat.is_trained and prob > 0) else "rules"

    return CategorizeSuggestResponse(
        suggested_category=category,
        confidence=confidence,
        all_categories=get_all_categories(),
        source=source,
    )


@router.post(
    "/corrections",
    summary="Log category correction",
    description="Logs when a user overrides a suggested category. Used for future ML model training. Data from all users improves the shared model.",
    responses={
        200: {"description": "Correction logged successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
    },
)
async def log_correction(
    data: CategorizeCorrectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Log when a user overrides a suggested category. Used for future ML training."""
    log = CorrectionLog(
        id=generate_uuid(),
        auth_user_id=current_user.id,
        description=data.description,
        merchant=data.merchant,
        suggested_category=data.suggested_category,
        corrected_category=data.corrected_category,
    )
    db.add(log)
    await db.commit()
    return {"status": "logged"}


@router.post(
    "/train",
    response_model=CategorizeTrainResponse,
    summary="Train categorization model",
    description="Trains the LightGBM categorization model on all logged corrections from all users. Requires minimum 30 samples. Returns training status, sample count, accuracy, and number of classes.",
    responses={
        200: {"description": "Training result"},
        401: {"description": "Unauthorized - invalid or missing token"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("2/hour")
async def train_model(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Train the ML categorization model on all logged corrections.

    Uses data from ALL users (corrections improve for everyone).
    Requires minimum 30 samples.
    """
    result = await db.execute(select(CorrectionLog))
    logs = result.scalars().all()

    if not logs:
        return CategorizeTrainResponse(status="no_data", samples=0, required=30)

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

    return CategorizeTrainResponse(
        status=stats["status"],
        samples=stats["samples"],
        accuracy=stats.get("accuracy"),
        num_classes=stats.get("num_classes"),
        required=stats.get("required"),
    )


@router.get(
    "/model-info",
    response_model=CategorizeModelInfo,
    summary="Get ML model info",
    description="Returns information about the current ML categorization model including training status, sample count, and whether a model exists on disk.",
    responses={
        200: {"description": "Model information"},
        401: {"description": "Unauthorized - invalid or missing token"},
    },
)
async def model_info(
    current_user = Depends(get_current_user),
):
    """Get info about the current ML model."""
    cat = get_categorizer()
    return CategorizeModelInfo(
        is_trained=cat.is_trained,
        training_samples=cat.training_samples,
        model_exists=cat.model is not None,
    )