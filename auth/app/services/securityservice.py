from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from ..config import settings


class SecurityService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.jwt_expire_minutes
            )

        to_encode.update({"exp": expire})

        if not settings.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY is not configured")

        encoded_jwt = jwt.encode(
            to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )
        return encoded_jwt

    def verify_token(self, token: Union[str, None]) -> Optional[str]:
        try:
            if not token or not settings.jwt_secret_key:
                return None

            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            username = payload.get("sub")
            if username is None or not isinstance(username, str):
                return None
            return username
        except JWTError:
            return None
