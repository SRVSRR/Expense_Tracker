"""Rate limiter configuration with per-endpoint tiers.

Buckets are keyed by the authenticated user when a Bearer token is present,
falling back to the client IP. The token's ``sub`` claim is used purely for
bucketing (NOT for authentication) and is extracted without signature
verification: limits are enforced after ``get_current_user`` has already
rejected invalid tokens, so forging a new ``sub`` requires a valid token.
Unauthenticated requests never reach the limiter.

slowapi buckets each decorated route independently, so one dashboard load
hitting every analytics endpoint consumes a single hit on each bucket.
All writes are single-item operations (no bulk endpoints exist), so the
WRITE tier below only binds automated abuse, not manual entry. A future
bulk-sync feature should get its own dedicated tier.
"""
import base64
import json
import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# Per-route tiers (see the API description in app/factory.py for the table).
AUTH_LIMIT = "60/minute"  # GET /api/auth/me
READ_LIMIT = "120/minute"  # GET list/detail endpoints
WRITE_LIMIT = "30/minute"  # POST/PUT/DELETE + corrections
ANALYTICS_LIMIT = "60/hour"  # forecast, budget, categorize/suggest
TRAIN_LIMIT = "2/hour"  # POST /api/categorize/train (ML training)


def user_or_ip_key(request) -> str:
    """Key rate-limit buckets by the Bearer token's ``sub`` claim, else IP."""
    auth = request.headers.get("Authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() == "bearer" and token:
        try:
            payload_b64 = token.split(".")[1]
            payload_b64 += "=" * (-len(payload_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass
    return get_remote_address(request)


# Disable rate limiting in test environments
if os.getenv("TESTING") == "1":

    class NoOpLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

        def hit(self, *args, **kwargs):
            pass

    limiter = NoOpLimiter()
else:
    limiter = Limiter(key_func=user_or_ip_key, default_limits=[])
