import uuid

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LoginMethod(str, Enum):
    EMAIL_PASSWORD = "email_password"


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class RevocationReason(str, Enum):
    USER_LOGOUT = "user_logout"
    ADMIN_REVOKED = "admin_revoked"
    TOKEN_EXPIRED = "token_expired"
    SECURITY = "security"
    PASSWORD_CHANGED = "password_changed"


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_version: str = "1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserRegisteredEvent(BaseEvent):
    user_id: int
    username: str
    email: str
    created_at: datetime
    event_type: str = "user.registered"


class UserAuthenticatedEvent(BaseEvent):
    user_id: int
    username: str
    login_method: LoginMethod
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    authenticated_at: datetime
    event_type: str = "user.authenticated"


class TokenRevokedEvent(BaseEvent):
    user_id: int
    token_type: TokenType
    reason: RevocationReason
    revoked_at: datetime
    event_type: str = "token.revoked"
