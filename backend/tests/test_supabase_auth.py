"""Unit tests for Supabase JWT verification (Phase 1)."""
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from jose import jwt, JWTError
from datetime import datetime, timedelta

# Set test environment before importing the module
os.environ["SUPABASE_JWKS_URL"] = "https://test.supabase.co/auth/v1/.well-known/jwks.json"
os.environ["SUPABASE_ISSUER"] = "https://test.supabase.co/auth/v1"

from app.utils.supabase_auth import verify_supabase_token, get_signing_key, get_jwks


class TestSupabaseJWTVerification:
    """Tests for Supabase JWT verification logic."""

    @pytest.fixture
    def sample_jwks(self):
        """A sample JWKS response with one RSA key."""
        # This is a test-only RSA public key (not for production use)
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "test-key-1",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "xAUPeSgY0Xa2QyLkRqN3dM4vK5hZ8bF2cE9dG7hJ1kL4mN6pQ8rT0vW3xY5zA2cE",
                    "e": "AQAB"
                }
            ]
        }

    @pytest.fixture
    def valid_token(self):
        """Create a valid test token with a known key."""
        # For testing, we'll use a simple approach - the actual key doesn't matter
        # since we mock the JWKS fetching
        payload = {
            "sub": "test-user-id-123",
            "email": "test@example.com",
            "aud": "authenticated",
            "iss": "https://test.supabase.co/auth/v1",
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
        }
        # Sign with a dummy key - we'll mock the verification anyway
        return jwt.encode(payload, "dummy-secret", algorithm="HS256")

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_get_jwks_caches_response(self, mock_client_class, sample_jwks):
        """Test that JWKS is fetched and cached."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_response = AsyncMock()
        mock_response.json = MagicMock(return_value=sample_jwks)
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # First call
        result1 = await get_jwks()
        assert result1 == sample_jwks
        assert mock_client.get.call_count == 1

        # Second call should use cache
        result2 = await get_jwks()
        assert result2 == sample_jwks
        assert mock_client.get.call_count == 1  # Still 1, cached

    def test_get_signing_key_finds_matching_kid(self, sample_jwks):
        """Test that the correct key is extracted from JWKS."""
        # Create a token with kid header
        token = jwt.encode({"sub": "test"}, "dummy", algorithm="HS256", headers={"kid": "test-key-1"})

        key = get_signing_key(token, sample_jwks)
        # The function returns an RSAKey object from jose
        assert key is not None
        # Verify the key works by checking it's an RSAKey type
        assert type(key).__name__ in ("RSAKey", "CryptographyRSAKey")

    def test_get_signing_key_raises_on_missing_kid(self, sample_jwks):
        """Test error when token has no kid header."""
        token = jwt.encode({"sub": "test"}, "dummy", algorithm="HS256")  # No kid header

        with pytest.raises(JWTError, match="Token missing kid header"):
            get_signing_key(token, sample_jwks)

    def test_get_signing_key_raises_on_unknown_kid(self, sample_jwks):
        """Test error when kid not found in JWKS."""
        token = jwt.encode({"sub": "test"}, "dummy", algorithm="HS256", headers={"kid": "unknown-key"})

        with pytest.raises(JWTError, match="Signing key not found for kid: unknown-key"):
            get_signing_key(token, sample_jwks)

    @pytest.mark.asyncio
    async def test_verify_supabase_token_valid(self, sample_jwks):
        """Test that a valid token is accepted."""
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "aud": "authenticated",
            "iss": "https://test.supabase.co/auth/v1",
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        }
        token = "dummy-token-with-kid-header"

        with patch("app.utils.supabase_auth.get_jwks", return_value=sample_jwks):
            with patch("app.utils.supabase_auth.get_signing_key") as mock_get_key:
                mock_key = MagicMock()
                mock_get_key.return_value = mock_key

                with patch("jose.jwt.decode", return_value=payload) as mock_decode:
                    result = await verify_supabase_token(token)
                    assert result["sub"] == "user-123"
                    assert result["email"] == "test@example.com"
                    mock_decode.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_supabase_token_rejects_expired(self, sample_jwks):
        """Test that expired tokens are rejected."""
        token = "expired-token"

        with patch("app.utils.supabase_auth.get_jwks", return_value=sample_jwks):
            with patch("app.utils.supabase_auth.get_signing_key") as mock_get_key:
                mock_key = MagicMock()
                mock_get_key.return_value = mock_key

                with patch("jose.jwt.decode", side_effect=JWTError("Signature has expired")):
                    with pytest.raises(JWTError):
                        await verify_supabase_token(token)

    @pytest.mark.asyncio
    async def test_verify_supabase_token_rejects_wrong_audience(self, sample_jwks):
        """Test that tokens with wrong audience are rejected."""
        token = "wrong-audience-token"

        with patch("app.utils.supabase_auth.get_jwks", return_value=sample_jwks):
            with patch("app.utils.supabase_auth.get_signing_key") as mock_get_key:
                mock_key = MagicMock()
                mock_get_key.return_value = mock_key

                with patch("jose.jwt.decode", side_effect=JWTError("Invalid audience")):
                    with pytest.raises(JWTError):
                        await verify_supabase_token(token)

    @pytest.mark.asyncio
    async def test_verify_supabase_token_rejects_wrong_issuer(self, sample_jwks):
        """Test that tokens with wrong issuer are rejected."""
        token = "wrong-issuer-token"

        with patch("app.utils.supabase_auth.get_jwks", return_value=sample_jwks):
            with patch("app.utils.supabase_auth.get_signing_key") as mock_get_key:
                mock_key = MagicMock()
                mock_get_key.return_value = mock_key

                with patch("jose.jwt.decode", side_effect=JWTError("Invalid issuer")):
                    with pytest.raises(JWTError):
                        await verify_supabase_token(token)

    @pytest.mark.asyncio
    async def test_verify_supabase_token_rejects_tampered(self, sample_jwks):
        """Test that tampered tokens are rejected."""
        token = "tampered-token"

        with patch("app.utils.supabase_auth.get_jwks", return_value=sample_jwks):
            with patch("app.utils.supabase_auth.get_signing_key") as mock_get_key:
                mock_key = MagicMock()
                mock_get_key.return_value = mock_key

                with patch("jose.jwt.decode", side_effect=JWTError("Invalid signature")):
                    with pytest.raises(JWTError):
                        await verify_supabase_token(token)


# Integration-style test using a real RS256 key pair (more realistic)
class TestSupabaseJWTWithRealKey:
    """Integration-style tests using a real RSA key pair."""

    @pytest.fixture
    def rsa_key_pair(self):
        """Generate a real RSA key pair for testing."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private_pem, public_pem

    @pytest.mark.asyncio
    async def test_real_rsa_token_verification(self, rsa_key_pair):
        """Test end-to-end with real RSA keys."""
        private_pem, public_pem = rsa_key_pair

        # Use a far future expiration to avoid clock skew issues
        payload = {
            "sub": "real-user-456",
            "email": "real@example.com",
            "aud": "authenticated",
            "iss": "https://test.supabase.co/auth/v1",
            "exp": int((datetime.utcnow() + timedelta(days=1)).timestamp()),
        }
        token = jwt.encode(payload, private_pem, algorithm="RS256", headers={"kid": "real-key-1"})

        # Build JWKS with the real public key
        from cryptography.hazmat.primitives import serialization
        public_key = serialization.load_pem_public_key(public_pem)
        numbers = public_key.public_numbers()
        n = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
        e = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
        import base64
        n_b64 = base64.urlsafe_b64encode(n).decode().rstrip("=")
        e_b64 = base64.urlsafe_b64encode(e).decode().rstrip("=")

        jwks = {
            "keys": [{
                "kty": "RSA",
                "kid": "real-key-1",
                "use": "sig",
                "alg": "RS256",
                "n": n_b64,
                "e": e_b64
            }]
        }

        # Verify using our function
        with patch("app.utils.supabase_auth.get_jwks", return_value=jwks):
            result = await verify_supabase_token(token)
            assert result["sub"] == "real-user-456"