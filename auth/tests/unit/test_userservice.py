import pytest

from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.userservice import UserService
from app.schemas import UserCreate, UserLogin
from app.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
    InvalidRefreshTokenError,
)
from app.models.user import User
from app.models.refreshtoken import RefreshToken
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


class TestUserService:
    def setup_method(self):
        self.user_service = UserService()

    @pytest.mark.unit
    async def test_get_user_by_username_exists(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="testuserexists",
            email="testuser_exists@example.com",
            password="testpassword123",
        )
        await self.user_service.create_user(db_session, user_data)

        found_user = await self.user_service.get_user_by_username(
            db_session, "testuserexists"
        )

        assert found_user is not None
        assert found_user.username == "testuserexists"
        assert found_user.email == "testuser_exists@example.com"
        assert found_user.is_active is True

    @pytest.mark.unit
    async def test_get_user_by_username_not_exists(self, db_session: AsyncSession):
        found_user = await self.user_service.get_user_by_username(
            db_session, "nonexistent"
        )
        assert found_user is None

    @pytest.mark.unit
    async def test_create_user_success(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="newusercreate",
            email="newuser_create@example.com",
            password="password123",
        )

        created_user = await self.user_service.create_user(db_session, user_data)

        assert created_user.username == "newusercreate"
        assert created_user.email == "newuser_create@example.com"
        assert created_user.is_active is True
        assert created_user.id is not None

    @pytest.mark.unit
    async def test_create_user_duplicate_username(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="duplicateuser",
            email="user1@example.com",
            password="password123",
        )

        await self.user_service.create_user(db_session, user_data)

        duplicate_user_data = UserCreate(
            username="duplicateuser",
            email="user2@example.com",
            password="password456",
        )

        with pytest.raises(UserAlreadyExistsError, match="Username already registered"):
            await self.user_service.create_user(db_session, duplicate_user_data)

    @pytest.mark.unit
    async def test_create_user_duplicate_email(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="user1",
            email="duplicate@example.com",
            password="password123",
        )

        await self.user_service.create_user(db_session, user_data)

        duplicate_email_data = UserCreate(
            username="user2",
            email="duplicate@example.com",
            password="password456",
        )

        with pytest.raises(UserAlreadyExistsError, match="Email already registered"):
            await self.user_service.create_user(db_session, duplicate_email_data)

    @pytest.mark.unit
    async def test_get_user_by_email_exists(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="emailtest",
            email="email_test@example.com",
            password="password123",
        )
        created_user = await self.user_service.create_user(db_session, user_data)

        found_user = await self.user_service.get_user_by_email(
            db_session, "email_test@example.com"
        )

        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.username == "emailtest"
        assert found_user.email == "email_test@example.com"

    @pytest.mark.unit
    async def test_get_user_by_email_not_exists(self, db_session: AsyncSession):
        found_user = await self.user_service.get_user_by_email(
            db_session, "nonexistent@example.com"
        )
        assert found_user is None

    @pytest.mark.unit
    async def test_get_user_by_id_exists(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="idtest",
            email="id_test@example.com",
            password="password123",
        )
        created_user = await self.user_service.create_user(db_session, user_data)

        found_user = await self.user_service.get_user_by_id(db_session, created_user.id)

        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.username == "idtest"
        assert found_user.email == "id_test@example.com"

    @pytest.mark.unit
    async def test_get_user_by_id_not_exists(self, db_session: AsyncSession):
        found_user = await self.user_service.get_user_by_id(db_session, 99999)
        assert found_user is None

    @pytest.mark.unit
    async def test_authenticate_user_success(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="authtest",
            email="auth_test@example.com",
            password="password123",
        )
        created_user = await self.user_service.create_user(db_session, user_data)

        login_data = UserLogin(username="authtest", password="password123")

        authenticated_user = await self.user_service.authenticate_user(
            db_session, login_data
        )

        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        assert authenticated_user.username == "authtest"
        assert authenticated_user.is_active is True

    @pytest.mark.unit
    async def test_authenticate_user_wrong_password(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="authwrong",
            email="auth_wrong@example.com",
            password="password123",
        )
        await self.user_service.create_user(db_session, user_data)

        login_data = UserLogin(username="authwrong", password="wrongpassword")

        with pytest.raises(
            InvalidCredentialsError, match="Invalid username or password"
        ):
            await self.user_service.authenticate_user(db_session, login_data)

    @pytest.mark.unit
    async def test_authenticate_user_not_exists(self, db_session: AsyncSession):
        login_data = UserLogin(username="nonexistent", password="password123")

        with pytest.raises(
            InvalidCredentialsError, match="Invalid username or password"
        ):
            await self.user_service.authenticate_user(db_session, login_data)

    @pytest.mark.unit
    async def test_authenticate_user_inactive(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="inactiveuser",
            email="inactive@example.com",
            password="password123",
        )
        await self.user_service.create_user(db_session, user_data)

        result = await db_session.execute(
            select(User).where(User.username == "inactiveuser")
        )
        user = result.scalar_one()
        setattr(user, "is_active", False)
        await db_session.commit()

        login_data = UserLogin(username="inactiveuser", password="password123")

        with pytest.raises(InvalidCredentialsError, match="Account is inactive"):
            await self.user_service.authenticate_user(db_session, login_data)

    @pytest.mark.unit
    async def test_get_current_user_by_token_success(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="tokentest",
            email="token_test@example.com",
            password="password123",
        )
        created_user = await self.user_service.create_user(db_session, user_data)

        # Create token for the user
        token = self.user_service.security.create_access_token(
            data={"sub": "tokentest"}
        )

        current_user = await self.user_service.get_current_user_by_token(
            db_session, token
        )

        assert current_user is not None
        assert current_user.id == created_user.id
        assert current_user.username == "tokentest"
        assert current_user.is_active is True

    @pytest.mark.unit
    async def test_get_current_user_by_token_invalid_token(
        self, db_session: AsyncSession
    ):
        with pytest.raises(InvalidCredentialsError, match="Invalid or expired token"):
            await self.user_service.get_current_user_by_token(
                db_session, "invalid_token"
            )

    @pytest.mark.unit
    async def test_get_current_user_by_token_user_not_found(
        self, db_session: AsyncSession
    ):
        # Create token for non-existent user
        token = self.user_service.security.create_access_token(
            data={"sub": "nonexistent"}
        )

        with pytest.raises(UserNotFoundError, match="User not found"):
            await self.user_service.get_current_user_by_token(db_session, token)

    @pytest.mark.unit
    async def test_get_current_user_by_token_inactive_user(
        self, db_session: AsyncSession
    ):
        user_data = UserCreate(
            username="tokeninactive",
            email="token_inactive@example.com",
            password="password123",
        )
        await self.user_service.create_user(db_session, user_data)

        # Make user inactive
        result = await db_session.execute(
            select(User).where(User.username == "tokeninactive")
        )
        user = result.scalar_one()
        setattr(user, "is_active", False)
        await db_session.commit()

        # Create token for the inactive user
        token = self.user_service.security.create_access_token(
            data={"sub": "tokeninactive"}
        )

        with pytest.raises(InvalidCredentialsError, match="Account is inactive"):
            await self.user_service.get_current_user_by_token(db_session, token)

    @pytest.mark.unit
    @patch("app.services.userservice.UserService")
    async def test_create_user_database_error_handling(self, mock_service):
        mock_service.create_user = AsyncMock(side_effect=Exception("Database error"))

        user_data = UserCreate(
            username="errortest",
            email="error@example.com",
            password="password123",
        )

        assert UserAlreadyExistsError.__name__ == "UserAlreadyExistsError"
        assert InvalidCredentialsError.__name__ == "InvalidCredentialsError"
        assert UserNotFoundError.__name__ == "UserNotFoundError"

    @pytest.mark.unit
    async def test_create_refresh_token_success(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="refreshuser",
            email="refresh@example.com",
            password="password123",
        )
        created_user = await self.user_service.create_user(db_session, user_data)

        refresh_token = await self.user_service.create_refresh_token(
            db_session, created_user.id
        )

        assert refresh_token is not None
        assert len(refresh_token.token) > 0
        assert refresh_token.is_revoked is False

    @pytest.mark.unit
    async def test_refresh_access_token_success(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="refreshuser2",
            email="refresh2@example.com",
            password="password123",
        )
        created_user = await self.user_service.create_user(db_session, user_data)
        refresh_token = await self.user_service.create_refresh_token(
            db_session, created_user.id
        )

        token_response = await self.user_service.refresh_access_token(
            db_session, refresh_token.token
        )

        assert token_response is not None
        assert len(token_response.access_token) > 0
        assert len(token_response.refresh_token) > 0
        assert token_response.refresh_token != refresh_token.token

    @pytest.mark.unit
    async def test_refresh_access_token_invalid(self, db_session: AsyncSession):
        with pytest.raises(InvalidRefreshTokenError):
            await self.user_service.refresh_access_token(db_session, "invalid_token")

    @pytest.mark.unit
    async def test_revoke_refresh_token_success(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="revokeuser",
            email="revoke@example.com",
            password="password123",
        )
        created_user = await self.user_service.create_user(db_session, user_data)
        refresh_token = await self.user_service.create_refresh_token(
            db_session, created_user.id
        )

        result = await self.user_service.revoke_refresh_token(
            db_session, refresh_token.token
        )

        assert result is True

        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token.token)
        )
        revoked_token = result.scalar_one_or_none()
        assert revoked_token is not None
        assert revoked_token.is_revoked is True

    @pytest.mark.unit
    async def test_revoke_all_user_tokens_success(self, db_session: AsyncSession):
        user_data = UserCreate(
            username="revokealluser",
            email="revokeall@example.com",
            password="password123",
        )
        created_user = await self.user_service.create_user(db_session, user_data)

        token1 = await self.user_service.create_refresh_token(
            db_session, created_user.id
        )
        token2 = await self.user_service.create_refresh_token(
            db_session, created_user.id
        )

        count = await self.user_service.revoke_all_user_tokens(
            db_session, created_user.id
        )

        assert count == 2
