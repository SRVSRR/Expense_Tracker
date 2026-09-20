"""Tests for circuit breaker and JWKS cache."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.utils.circuit_breaker import CircuitBreaker, CircuitState, supabase_jwks_breaker
from app.utils.exceptions import ExternalServiceError
import app.utils.supabase_auth as supabase_auth


def test_breaker_initial_state():
    breaker = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60.0)
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


@pytest.mark.asyncio
async def test_breaker_opens_after_threshold():
    breaker = CircuitBreaker(name="test-breaker", failure_threshold=3, recovery_timeout=60.0)

    async def failing_func():
        raise RuntimeError("downstream failure")

    # First 2 failures keep closed (but increment count)
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await breaker.call(failing_func)
        assert breaker.state == CircuitState.CLOSED

    # 3rd failure opens
    with pytest.raises(RuntimeError):
        await breaker.call(failing_func)
    assert breaker.state == CircuitState.OPEN
    assert breaker.failure_count == 3

    # Next call fast-fails with ExternalServiceError
    with pytest.raises(ExternalServiceError) as exc:
        await breaker.call(failing_func)
    assert exc.value.code == "EXTERNAL_SERVICE_UNAVAILABLE"
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_breaker_resets_on_success():
    breaker = CircuitBreaker(name="test-reset", failure_threshold=3, recovery_timeout=60.0)

    async def failing_func():
        raise RuntimeError("fail")

    async def success_func():
        return "ok"

    # Cause 2 failures
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await breaker.call(failing_func)
    assert breaker.failure_count == 2

    # Success resets
    result = await breaker.call(success_func)
    assert result == "ok"
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


@pytest.mark.asyncio
async def test_breaker_half_open_after_timeout():
    breaker = CircuitBreaker(name="test-half-open", failure_threshold=2, recovery_timeout=0.1)

    async def failing_func():
        raise RuntimeError("fail")

    # Trip breaker
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await breaker.call(failing_func)
    assert breaker.state == CircuitState.OPEN

    # Should still be open immediately
    with pytest.raises(ExternalServiceError):
        await breaker.call(failing_func)

    # Wait for timeout
    await asyncio.sleep(0.15)

    # Next call should be allowed (half-open)
    async def success_func():
        return "recovered"

    result = await breaker.call(success_func)
    assert result == "recovered"
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_jwks_cache_and_breaker_integration(monkeypatch):
    # Clear cache
    supabase_auth._clear_jwks_cache()
    assert supabase_auth._jwks_cache is None
    assert supabase_jwks_breaker.state == CircuitState.CLOSED

    # Mock successful fetch
    from unittest.mock import Mock

    mock_jwks = {"keys": [{"kid": "test", "kty": "RSA", "n": "abc", "e": "AQAB"}]}
    mock_resp = Mock()
    mock_resp.json.return_value = mock_jwks
    mock_resp.raise_for_status = Mock()

    monkeypatch.setenv("SUPABASE_JWKS_URL", "https://example.supabase.co/auth/v1/.well-known/jwks.json")

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = await supabase_auth.get_jwks()
        assert result == mock_jwks
        assert supabase_auth._jwks_cache == mock_jwks

        # Second call should use cache, not fetch again
        mock_client.get.reset_mock()
        result2 = await supabase_auth.get_jwks()
        assert result2 == mock_jwks
        mock_client.get.assert_not_called()

    # Cleanup
    supabase_auth._clear_jwks_cache()


@pytest.mark.asyncio
async def test_jwks_breaker_wraps_http_errors(monkeypatch):
    supabase_auth._clear_jwks_cache()
    monkeypatch.setenv("SUPABASE_JWKS_URL", "https://example.supabase.co/auth/v1/.well-known/jwks.json")

    import httpx

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = httpx.ConnectError("connection failed")
        mock_client_cls.return_value = mock_client

        # First few calls count as failures but still raise original wrapped as ExternalServiceError
        with pytest.raises(ExternalServiceError):
            await supabase_auth.get_jwks()

    supabase_auth._clear_jwks_cache()
