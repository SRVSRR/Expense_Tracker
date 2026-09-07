"""Prediction caching service — reads/writes the predictions table."""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Prediction

# TTL per prediction type (hours)
TTL_HOURS = {
    "cashflow": 24,
    "runway": 12,
    "anomaly": 24,
    "budget": 168,  # 7 days
}


async def get_cached_prediction(
    db: AsyncSession,
    user_id: str,
    pred_type: str,
) -> Optional[dict]:
    """Return cached prediction if it exists and hasn't expired, else None."""
    now = datetime.utcnow()
    result = await db.execute(
        select(Prediction).where(
            Prediction.auth_user_id == user_id,
            Prediction.type == pred_type,
            Prediction.valid_until > now,
        ).order_by(Prediction.generated_at.desc()).limit(1)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return json.loads(row.data)


async def store_prediction(
    db: AsyncSession,
    user_id: str,
    pred_type: str,
    data: dict,
    ttl_hours: Optional[int] = None,
) -> None:
    """Write a prediction to the cache, invalidating any previous entry of same type."""
    if ttl_hours is None:
        ttl_hours = TTL_HOURS.get(pred_type, 24)

    now = datetime.utcnow()

    # Delete old predictions of this type for this user
    await db.execute(
        delete(Prediction).where(
            Prediction.auth_user_id == user_id,
            Prediction.type == pred_type,
        )
    )

    # Insert new one
    prediction = Prediction(
        id=str(uuid.uuid4()),
        auth_user_id=user_id,
        type=pred_type,
        data=json.dumps(data),
        generated_at=now,
        valid_until=now + timedelta(hours=ttl_hours),
    )
    db.add(prediction)
    await db.commit()


async def invalidate_predictions(
    db: AsyncSession,
    user_id: str,
    pred_type: Optional[str] = None,
) -> None:
    """Invalidate cached predictions. If pred_type is given, only invalidate that type."""
    stmt = delete(Prediction).where(Prediction.auth_user_id == user_id)
    if pred_type:
        stmt = stmt.where(Prediction.type == pred_type)
    await db.execute(stmt)
    await db.commit()
