from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from ..models.user import User
from ..schemas import UserCreate, UserLogin, UserResponse
from .securityservice import SecurityService
from ..exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
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
