import pytest

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from app.models.refreshtoken import RefreshToken
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


class TestRefreshTokenEndpoints:

    @pytest.mark.integration
    async def test_login_returns_refresh_token(
        self, client: AsyncClient, test_user_data
    ):
        await client.post("/auth/register", json=test_user_data)

        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"],
        }

        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    @pytest.mark.integration
    async def test_refresh_token_success(self, client: AsyncClient, test_user_data):
        await client.post("/auth/register", json=test_user_data)

        login_response = await client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )
        login_data = login_response.json()
        original_refresh_token = login_data["refresh_token"]

        refresh_response = await client.post(
            "/auth/refresh", json={"refresh_token": original_refresh_token}
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        refresh_data = refresh_response.json()

        assert "access_token" in refresh_data
        assert "refresh_token" in refresh_data
        assert "expires_in" in refresh_data
        assert refresh_data["token_type"] == "bearer"
        assert refresh_data["refresh_token"] != original_refresh_token

    @pytest.mark.integration
    async def test_refresh_token_invalid(self, client: AsyncClient):
        response = await client.post(
            "/auth/refresh", json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Invalid or expired refresh token" in data["detail"]

    @pytest.mark.integration
    async def test_refresh_token_revoked_after_use(
        self, client: AsyncClient, db_session: AsyncSession, test_user_data
    ):
        await client.post("/auth/register", json=test_user_data)

        login_response = await client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        await client.post("/auth/refresh", json={"refresh_token": refresh_token})

        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        db_refresh_token = result.scalar_one_or_none()

        assert db_refresh_token is not None
        assert db_refresh_token.is_revoked is True

    @pytest.mark.integration
    async def test_refresh_token_twice_fails(self, client: AsyncClient, test_user_data):
        await client.post("/auth/register", json=test_user_data)

        login_response = await client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        first_refresh = await client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert first_refresh.status_code == status.HTTP_200_OK

        second_refresh = await client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert second_refresh.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    async def test_refresh_token_missing(self, client: AsyncClient):
        response = await client.post("/auth/refresh", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
