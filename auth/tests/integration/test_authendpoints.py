import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from app.schemas import UserCreate, UserLogin, TokenData
from app.models.user import User
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


class TestAuthEndpoints:

    @pytest.mark.integration
    async def test_register_user_success(self, client: AsyncClient, test_user_data):
        print(f"Registering user with data: {test_user_data}")
        response = await client.post("/auth/register", json=test_user_data)

        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # Ensure password is not returned

    @pytest.mark.integration
    async def test_register_user_duplicate_username(
        self, client: AsyncClient, test_user_data
    ):
        await client.post("/auth/register", json=test_user_data)

        duplicate_data = test_user_data.copy()
        duplicate_data["email"] = "different@example.com"

        response = await client.post("/auth/register", json=duplicate_data)
        assert response.status_code == status.HTTP_409_CONFLICT

        data = response.json()
        assert "Username already registered" in data["detail"]

    @pytest.mark.integration
    async def test_register_user_duplicate_email(
        self, client: AsyncClient, test_user_data
    ):
        await client.post("/auth/register", json=test_user_data)

        duplicate_data = test_user_data.copy()
        duplicate_data["username"] = "differentuser"

        response = await client.post("/auth/register", json=duplicate_data)
        assert response.status_code == status.HTTP_409_CONFLICT

        data = response.json()
        assert "Email already registered" in data["detail"]

    @pytest.mark.integration
    async def test_register_user_invalid_data(self, client: AsyncClient):
        invalid_data = {
            "username": "ab",
            "email": "invalid-email",
            "password": "123",
        }

        response = await client.post("/auth/register", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.integration
    async def test_login_success(self, client: AsyncClient, test_user_data):
        await client.post("/auth/register", json=test_user_data)

        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"],
        }

        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    @pytest.mark.integration
    async def test_login_invalid_username(self, client: AsyncClient):
        login_data = {"username": "nonexistent", "password": "password123"}

        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        data = response.json()
        assert "Invalid username or password" in data["detail"]

    @pytest.mark.integration
    async def test_login_invalid_password(self, client: AsyncClient, test_user_data):
        await client.post("/auth/register", json=test_user_data)

        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword",
        }

        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        data = response.json()
        assert "Invalid username or password" in data["detail"]

    @pytest.mark.integration
    async def test_login_inactive_user(
        self, client: AsyncClient, db_session: AsyncSession, test_user_data
    ):
        # Register user first
        await client.post("/auth/register", json=test_user_data)

        result = await db_session.execute(
            select(User).where(User.username == test_user_data["username"])
        )
        user = result.scalar_one()
        setattr(user, "is_active", False)
        await db_session.commit()

        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"],
        }

        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        data = response.json()
        assert "Account is inactive" in data["detail"]

    @pytest.mark.integration
    async def test_verify_token_success(self, client: AsyncClient, test_user_data):
        await client.post("/auth/register", json=test_user_data)

        login_response = await client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        verify_data = {"token": token}
        response = await client.post("/auth/verify", json=verify_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True

    @pytest.mark.integration
    async def test_verify_token_invalid(self, client: AsyncClient):
        verify_data = {"token": "invalid_token"}
        response = await client.post("/auth/verify", json=verify_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Invalid or expired token" in data["detail"]

    @pytest.mark.integration
    async def test_verify_token_missing(self, client: AsyncClient):
        verify_data = {}
        response = await client.post("/auth/verify", json=verify_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "Token is required" in data["detail"]

    @pytest.mark.integration
    async def test_get_current_user_success(self, client: AsyncClient, test_user_data):
        await client.post("/auth/register", json=test_user_data)

        login_response = await client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/auth/me", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True

    @pytest.mark.integration
    async def test_get_current_user_missing_header(self, client: AsyncClient):
        response = await client.get("/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Authorization header missing or invalid" in data["detail"]

    @pytest.mark.integration
    async def test_get_current_user_invalid_header_format(self, client: AsyncClient):
        headers = {"Authorization": "InvalidFormat token"}
        response = await client.get("/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Authorization header missing or invalid" in data["detail"]

    @pytest.mark.integration
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Invalid or expired token" in data["detail"]

    @pytest.mark.integration
    async def test_get_current_user_inactive_user(
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
        token = login_response.json()["access_token"]

        result = await db_session.execute(
            select(User).where(User.username == test_user_data["username"])
        )
        user = result.scalar_one()
        setattr(user, "is_active", False)
        await db_session.commit()

        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Account is inactive" in data["detail"]

    @pytest.mark.integration
    async def test_complete_auth_flow(self, client: AsyncClient, test_user_data):
        register_response = await client.post("/auth/register", json=test_user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"],
        }
        login_response = await client.post("/auth/login", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        verify_response = await client.post("/auth/verify", json={"token": token})
        assert verify_response.status_code == status.HTTP_200_OK

        headers = {"Authorization": f"Bearer {token}"}
        me_response = await client.get("/auth/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK

        register_data = register_response.json()
        verify_data = verify_response.json()
        me_data = me_response.json()

        assert (
            register_data["username"] == verify_data["username"] == me_data["username"]
        )
        assert register_data["email"] == verify_data["email"] == me_data["email"]
        assert register_data["id"] == verify_data["id"] == me_data["id"]
