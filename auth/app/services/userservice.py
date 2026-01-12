from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from typing import Optional
from ..models.user import User
from ..models.refreshtoken import RefreshToken
from ..schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshTokenResponse,
)
from .securityservice import SecurityService
from ..config import settings
from ..exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
    InvalidRefreshTokenError,
)


class UserService:
    def __init__(self):
        self.security = SecurityService()

    async def get_user_by_username(
        self, db: AsyncSession, username: str
    ) -> Optional[UserResponse]:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user:
            await db.refresh(user)
            return UserResponse.model_validate(user)
        return None

    async def get_user_by_email(
        self, db: AsyncSession, email: str
    ) -> Optional[UserResponse]:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            return UserResponse.model_validate(user)
        return None

    async def get_user_by_id(
        self, db: AsyncSession, user_id: int
    ) -> Optional[UserResponse]:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            return UserResponse.model_validate(user)
        return None

    async def create_user(
        self, db: AsyncSession, user_data: UserCreate
    ) -> UserResponse:
        existing_user = await self.get_user_by_username(db, user_data.username)
        if existing_user:
            raise UserAlreadyExistsError("Username already registered")

        existing_email = await self.get_user_by_email(db, user_data.email)
        if existing_email:
            raise UserAlreadyExistsError("Email already registered")

        hashed_password = self.security.hash_password(user_data.password)

        db_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            is_active=True,
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return UserResponse.model_validate(db_user)

    async def authenticate_user(
        self, db: AsyncSession, login_data: UserLogin
    ) -> UserResponse:
        user = await self.get_user_by_username(db, login_data.username)
        if not user:
            raise InvalidCredentialsError("Invalid username or password")

        if not user.is_active:
            raise InvalidCredentialsError("Account is inactive")

        result = await db.execute(
            select(User).where(User.username == login_data.username)
        )
        db_user = result.scalar_one_or_none()

        if not db_user:
            raise InvalidCredentialsError("Invalid username or password")

        await db.refresh(db_user)
        password_hash = str(db_user.password_hash)

        if not self.security.verify_password(login_data.password, password_hash):
            raise InvalidCredentialsError("Invalid username or password")

        return user

    async def get_current_user_by_token(
        self, db: AsyncSession, token: str
    ) -> UserResponse:
        username = self.security.verify_token(token)
        if not username:
            raise InvalidCredentialsError("Invalid or expired token")

        user = await self.get_user_by_username(db, username)
        if not user:
            raise UserNotFoundError("User not found")

        if not user.is_active:
            raise InvalidCredentialsError("Account is inactive")

        return user

    async def create_refresh_token(
        self, db: AsyncSession, user_id: int
    ) -> RefreshTokenResponse:
        token_string = self.security.create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        refresh_token = RefreshToken(
            token=token_string, user_id=user_id, expires_at=expires_at
        )

        db.add(refresh_token)
        await db.commit()
        await db.refresh(refresh_token)

        return RefreshTokenResponse(
            token=str(refresh_token.token),
            expires_at=expires_at,
            is_revoked=bool(refresh_token.is_revoked),
        )

    async def refresh_access_token(
        self, db: AsyncSession, refresh_token_string: str
    ) -> TokenResponse:
        result = await db.execute(
            select(RefreshToken)
            .where(RefreshToken.token == refresh_token_string)
            .where(RefreshToken.is_revoked.is_(False))
        )
        refresh_token = result.scalar_one_or_none()

        if refresh_token is None:
            raise InvalidRefreshTokenError("Invalid or expired refresh token")

        await db.refresh(refresh_token)

        expires_at = getattr(refresh_token, "expires_at")
        if expires_at < datetime.now(timezone.utc):
            raise InvalidRefreshTokenError("Invalid or expired refresh token")

        user_id = getattr(refresh_token, "user_id")
        user = await self.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise InvalidRefreshTokenError("User not found or inactive")

        setattr(refresh_token, "is_revoked", True)
        await db.commit()

        new_refresh_token = await self.create_refresh_token(db, user.id)
        access_token = self.security.create_access_token(data={"sub": user.username})

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token.token,
            expires_in=settings.jwt_expire_minutes * 60,
        )

    async def refresh_access_token_with_user(
        self, db: AsyncSession, refresh_token_string: str
    ) -> tuple[TokenResponse, UserResponse]:
        result = await db.execute(
            select(RefreshToken)
            .where(RefreshToken.token == refresh_token_string)
            .where(RefreshToken.is_revoked.is_(False))
        )
        refresh_token = result.scalar_one_or_none()

        if refresh_token is None:
            raise InvalidRefreshTokenError("Invalid or expired refresh token")

        await db.refresh(refresh_token)

        expires_at = getattr(refresh_token, "expires_at")
        if expires_at < datetime.now(timezone.utc):
            raise InvalidRefreshTokenError("Invalid or expired refresh token")

        user_id = getattr(refresh_token, "user_id")
        user = await self.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise InvalidRefreshTokenError("User not found or inactive")

        setattr(refresh_token, "is_revoked", True)
        await db.commit()

        new_refresh_token = await self.create_refresh_token(db, user.id)
        access_token = self.security.create_access_token(data={"sub": user.username})

        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token.token,
            expires_in=settings.jwt_expire_minutes * 60,
        )
        
        return token_response, user

    async def revoke_refresh_token(
        self, db: AsyncSession, refresh_token_string: str
    ) -> bool:
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token_string)
        )
        refresh_token = result.scalar_one_or_none()

        if refresh_token:
            setattr(refresh_token, "is_revoked", True)
            await db.commit()
            return True
        return False

    async def revoke_all_user_tokens(self, db: AsyncSession, user_id: int) -> int:
        result = await db.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.is_revoked.is_(False))
        )
        tokens = result.scalars().all()

        count = 0
        for token in tokens:
            setattr(token, "is_revoked", True)
            count += 1

        await db.commit()
        return count
