"""Simple async circuit breaker for external service calls.

Used to protect Supabase JWKS fetching from repeated failures. When the
downstream service is down, the breaker opens and fast-fails with
ExternalServiceError (503) instead of hammering the network.

States:
- CLOSED: normal operation, failures counted
- OPEN: service considered down, calls fast-fail
- HALF_OPEN: after timeout, allow one trial call

This is intentionally minimal — no external dependencies, per-process memory
only. Suitable for single-instance Render deployments. For multi-instance
you'd want a shared store (Redis).
"""

import asyncio
import time
from enum import Enum
from typing import Callable, TypeVar, Any
from functools import wraps

from app.utils.exceptions import ExternalServiceError

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Async circuit breaker with failure threshold and recovery timeout."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def _should_attempt_reset(self) -> bool:
        if self._state != CircuitState.OPEN:
            return False
        if self._last_failure_time is None:
            return False
        return (time.monotonic() - self._last_failure_time) >= self.recovery_timeout

    async def _on_success(self) -> None:
        async with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            self._half_open_calls = 0
            self._last_failure_time = None

    async def _on_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
            elif self._state == CircuitState.HALF_OPEN:
                # Trial failed, re-open
                self._state = CircuitState.OPEN

    async def _try_half_open(self) -> bool:
        """Check if we can transition OPEN -> HALF_OPEN and allow a trial call."""
        async with self._lock:
            if self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                return True
            return False

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute func through the breaker. Raises ExternalServiceError when open."""
        # Check if we should allow the call
        if self._state == CircuitState.OPEN:
            # Try to transition to half-open if timeout elapsed
            # need to avoid holding lock while checking time
            should_try = self._should_attempt_reset()
            if should_try:
                async with self._lock:
                    if self._state == CircuitState.OPEN and self._should_attempt_reset():
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0
            else:
                raise ExternalServiceError(
                    service=self.name,
                    message=f"External service '{self.name}' unavailable (circuit open)",
                )

        if self._state == CircuitState.HALF_OPEN:
            async with self._lock:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise ExternalServiceError(
                        service=self.name,
                        message=f"External service '{self.name}' unavailable (circuit open)",
                    )
                self._half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
        except ExternalServiceError:
            # Already a service error, count it but don't double-wrap
            await self._on_failure()
            raise
        except Exception as exc:
            # Network / HTTP errors from downstream count as failures
            await self._on_failure()
            # Wrap unexpected downstream errors as ExternalServiceError for 503 handling
            # unless it's clearly a programming error; we check httpx/jwt errors
            # For now, re-raise original for caller to handle, but still count failure
            # However spec expects 503 for Supabase outage — we wrap httpx errors
            import httpx

            if isinstance(exc, (httpx.HTTPError, httpx.TimeoutException)):
                raise ExternalServiceError(service=self.name, message=str(exc)) from exc
            raise
        else:
            await self._on_success()
            return result

    def reset(self) -> None:
        """Reset breaker to closed (useful for tests)."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0


# Global breaker for Supabase JWKS fetching (single instance)
supabase_jwks_breaker = CircuitBreaker(
    name="supabase",
    failure_threshold=3,
    recovery_timeout=60.0,
)


def circuit_breaker(
    breaker: CircuitBreaker,
):
    """Decorator to wrap an async function with a circuit breaker."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator
