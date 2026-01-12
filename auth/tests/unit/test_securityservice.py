import pytest

from datetime import datetime, timedelta
from freezegun import freeze_time
from jose import jwt
from app.services.securityservice import SecurityService
from app.config import settings


class TestSecurityService:
    def setup_method(self):
        self.security_service = SecurityService()

    @pytest.mark.unit
    def test_hash_password_generates_valid_hash(self):
        password = "TestPassword123"
        hashed = self.security_service.hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 50
        assert hashed != password
        assert hashed.startswith("$argon2")

    @pytest.mark.unit
    def test_hash_password_different_for_same_input(self):
        password = "TestPassword123"
        hash1 = self.security_service.hash_password(password)
        hash2 = self.security_service.hash_password(password)

        assert hash1 != hash2

    @pytest.mark.unit
    def test_verify_password_correct_password(self):
        password = "TestPassword123"
        hashed = self.security_service.hash_password(password)

        result = self.security_service.verify_password(password, hashed)

        assert result is True

    @pytest.mark.unit
    def test_verify_password_incorrect_password(self):
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = self.security_service.hash_password(password)

        result = self.security_service.verify_password(wrong_password, hashed)

        assert result is False

    @pytest.mark.unit
    def test_verify_password_empty_password(self):
        password = "TestPassword123"
        hashed = self.security_service.hash_password(password)

        result = self.security_service.verify_password("", hashed)

        assert result is False

    @pytest.mark.unit
    def test_create_access_token_valid_payload(self):
        data = {"sub": "testuser"}

        token = self.security_service.create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    @pytest.mark.unit
    def test_create_access_token_with_expiry(self):
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=15)

        token = self.security_service.create_access_token(
            data, expires_delta=expires_delta
        )

        assert (
            settings.jwt_secret_key is not None
        ), "JWT secret key must be configured for testing"

        decoded = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        assert "exp" in decoded
        assert "sub" in decoded
        assert decoded["sub"] == "testuser"

    @pytest.mark.unit
    def test_verify_token_valid_token(self):
        username = "testuser"
        data = {"sub": username}
        token = self.security_service.create_access_token(data)

        result = self.security_service.verify_token(token)

        assert result == username

    @pytest.mark.unit
    def test_verify_token_invalid_token(self):
        invalid_token = "invalid.token.here"

        result = self.security_service.verify_token(invalid_token)

        assert result is None

    @pytest.mark.unit
    def test_verify_token_malformed_token(self):
        malformed_token = "not-a-jwt-token"

        result = self.security_service.verify_token(malformed_token)

        assert result is None

    @pytest.mark.unit
    def test_verify_token_expired_token(self):
        username = "testuser"
        data = {"sub": username}

        with freeze_time("2024-01-01 12:00:00"):
            token = self.security_service.create_access_token(
                data, expires_delta=timedelta(seconds=1)
            )

        with freeze_time("2024-01-01 12:00:02"):
            result = self.security_service.verify_token(token)

        assert result is None

    @pytest.mark.unit
    def test_verify_token_wrong_secret(self):
        fake_token = jwt.encode(
            {"sub": "testuser", "exp": datetime.utcnow() + timedelta(minutes=30)},
            "wrong-secret",
            algorithm="HS256",
        )

        result = self.security_service.verify_token(fake_token)

        assert result is None

    @pytest.mark.unit
    def test_verify_token_no_sub_claim(self):
        data = {"user_id": "123"}
        token = self.security_service.create_access_token(data)

        result = self.security_service.verify_token(token)

        assert result is None

    @pytest.mark.unit
    def test_verify_token_empty_token(self):
        result = self.security_service.verify_token("")

        assert result is None

    @pytest.mark.unit
    def test_verify_token_none_token(self):
        result = self.security_service.verify_token(None)

        assert result is None

    @pytest.mark.unit
    def test_create_refresh_token_generates_token(self):
        refresh_token = self.security_service.create_refresh_token()

        assert refresh_token is not None
        assert len(refresh_token) > 0
        assert isinstance(refresh_token, str)

    @pytest.mark.unit
    def test_create_refresh_token_generates_unique_tokens(self):
        token1 = self.security_service.create_refresh_token()
        token2 = self.security_service.create_refresh_token()

        assert token1 != token2
