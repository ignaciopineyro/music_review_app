"""
Event definitions for the Music Review App microservices.
Contains all event schemas used for communication between services.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .messaging import EventBase


# =============================================================================
# Authentication Service Events
# =============================================================================


class UserRegisteredEvent(EventBase):
    """Event published when a new user registers"""

    user_id: str
    email: str
    username: str
    created_at: datetime
    is_active: bool = True

    def __init__(self, user_id: str, email: str, username: str, **kwargs):
        super().__init__(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            service_name="auth-service",
            event_type="user.registered",
            user_id=user_id,
            email=email,
            username=username,
            created_at=kwargs.get("created_at", datetime.utcnow()),
            **kwargs
        )


class UserLoginEvent(EventBase):
    """Event published when user logs in"""

    user_id: str
    email: str
    login_timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def __init__(self, user_id: str, email: str, **kwargs):
        super().__init__(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            service_name="auth-service",
            event_type="user.login",
            user_id=user_id,
            email=email,
            login_timestamp=datetime.utcnow(),
            **kwargs
        )


class UserLogoutEvent(EventBase):
    """Event published when user logs out"""

    user_id: str
    logout_timestamp: datetime
    session_duration_minutes: Optional[int] = None

    def __init__(self, user_id: str, **kwargs):
        super().__init__(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            service_name="auth-service",
            event_type="user.logout",
            user_id=user_id,
            logout_timestamp=datetime.utcnow(),
            **kwargs
        )


class TokenRevokedEvent(EventBase):
    """Event published when a JWT token is revoked"""

    user_id: str
    token_jti: str  # JWT ID
    revoked_at: datetime
    reason: Optional[str] = None

    def __init__(self, user_id: str, token_jti: str, **kwargs):
        super().__init__(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            service_name="auth-service",
            event_type="token.revoked",
            user_id=user_id,
            token_jti=token_jti,
            revoked_at=datetime.utcnow(),
            **kwargs
        )


class UserProfileUpdatedEvent(EventBase):
    """Event published when user profile is updated"""

    user_id: str
    updated_fields: list[str]
    updated_at: datetime

    def __init__(self, user_id: str, updated_fields: list[str], **kwargs):
        super().__init__(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            service_name="auth-service",
            event_type="user.profile_updated",
            user_id=user_id,
            updated_fields=updated_fields,
            updated_at=datetime.utcnow(),
            **kwargs
        )


# =============================================================================
# Reviews Service Events
# =============================================================================


class AlbumCreatedEvent(EventBase):
    """Event published when a new album is created"""

    album_id: str
    title: str
    artist: str
    year: int
    created_by_user_id: str
    created_at: datetime

    def __init__(
        self,
        album_id: str,
        title: str,
        artist: str,
        year: int,
        created_by_user_id: str,
        **kwargs
    ):
        super().__init__(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            service_name="reviews-service",
            event_type="album.created",
            album_id=album_id,
            title=title,
            artist=artist,
            year=year,
            created_by_user_id=created_by_user_id,
            created_at=datetime.utcnow(),
            **kwargs
        )


class AlbumUpdatedEvent(EventBase):
    """Event published when an album is updated"""

    album_id: str
    title: str
    artist: str
    year: int
    updated_by_user_id: str
    updated_at: datetime
    updated_fields: list[str]

    def __init__(
        self,
        album_id: str,
        title: str,
        artist: str,
        year: int,
        updated_by_user_id: str,
        updated_fields: list[str],
        **kwargs
    ):
        super().__init__(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            service_name="reviews-service",
            event_type="album.updated",
            album_id=album_id,
            title=title,
            artist=artist,
            year=year,
            updated_by_user_id=updated_by_user_id,
            updated_at=datetime.utcnow(),
            updated_fields=updated_fields,
            **kwargs
        )


class AlbumDeletedEvent(EventBase):
    """Event published when an album is deleted"""

    album_id: str
    title: str
    artist: str
    deleted_by_user_id: str
    deleted_at: datetime

    def __init__(
        self, album_id: str, title: str, artist: str, deleted_by_user_id: str, **kwargs
    ):
        super().__init__(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            service_name="reviews-service",
            event_type="album.deleted",
            album_id=album_id,
            title=title,
            artist=artist,
            deleted_by_user_id=deleted_by_user_id,
            deleted_at=datetime.utcnow(),
            **kwargs
        )


class ReviewCreatedEvent(EventBase):
    """Event published when a new review is created"""

    review_id: str
    album_id: str
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime

    def __init__(
        self, review_id: str, album_id: str, user_id: str, rating: int, **kwargs
    ):
        super().__init__(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            service_name="reviews-service",
            event_type="review.created",
            review_id=review_id,
            album_id=album_id,
            user_id=user_id,
            rating=rating,
            created_at=datetime.utcnow(),
            **kwargs
        )


class ReviewUpdatedEvent(EventBase):
    """Event published when a review is updated"""

    review_id: str
    album_id: str
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    updated_at: datetime
    updated_fields: list[str]

    def __init__(
        self,
        review_id: str,
        album_id: str,
        user_id: str,
        rating: int,
        updated_fields: list[str],
        **kwargs
    ):
        super().__init__(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            service_name="reviews-service",
            event_type="review.updated",
            review_id=review_id,
            album_id=album_id,
            user_id=user_id,
            rating=rating,
            updated_at=datetime.utcnow(),
            updated_fields=updated_fields,
            **kwargs
        )


class ReviewDeletedEvent(EventBase):
    """Event published when a review is deleted"""

    review_id: str
    album_id: str
    user_id: str
    deleted_at: datetime

    def __init__(self, review_id: str, album_id: str, user_id: str, **kwargs):
        super().__init__(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            service_name="reviews-service",
            event_type="review.deleted",
            review_id=review_id,
            album_id=album_id,
            user_id=user_id,
            deleted_at=datetime.utcnow(),
            **kwargs
        )


# =============================================================================
# RPC Request/Response Models
# =============================================================================


class ValidateTokenRequest(BaseModel):
    """RPC request to validate JWT token"""

    token: str
    required_permissions: Optional[list[str]] = None


class ValidateTokenResponse(BaseModel):
    """RPC response for token validation"""

    is_valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    permissions: Optional[list[str]] = None
    error: Optional[str] = None


class GetUserProfileRequest(BaseModel):
    """RPC request to get user profile"""

    user_id: str


class GetUserProfileResponse(BaseModel):
    """RPC response with user profile"""

    user_id: str
    email: str
    username: str
    created_at: datetime
    is_active: bool
    error: Optional[str] = None


# =============================================================================
# Event Registry
# =============================================================================

# Mapping of event types to their corresponding classes
EVENT_REGISTRY = {
    # Auth Service Events
    "user.registered": UserRegisteredEvent,
    "user.login": UserLoginEvent,
    "user.logout": UserLogoutEvent,
    "token.revoked": TokenRevokedEvent,
    "user.profile_updated": UserProfileUpdatedEvent,
    # Reviews Service Events
    "album.created": AlbumCreatedEvent,
    "album.updated": AlbumUpdatedEvent,
    "album.deleted": AlbumDeletedEvent,
    "review.created": ReviewCreatedEvent,
    "review.updated": ReviewUpdatedEvent,
    "review.deleted": ReviewDeletedEvent,
}


# =============================================================================
# Routing Keys
# =============================================================================


class RoutingKeys:
    """Centralized routing key definitions"""

    # Auth Service Routes
    USER_REGISTERED = "auth.user.registered"
    USER_LOGIN = "auth.user.login"
    USER_LOGOUT = "auth.user.logout"
    TOKEN_REVOKED = "auth.token.revoked"
    USER_PROFILE_UPDATED = "auth.user.profile_updated"

    # Reviews Service Routes
    ALBUM_CREATED = "reviews.album.created"
    ALBUM_UPDATED = "reviews.album.updated"
    ALBUM_DELETED = "reviews.album.deleted"
    REVIEW_CREATED = "reviews.review.created"
    REVIEW_UPDATED = "reviews.review.updated"
    REVIEW_DELETED = "reviews.review.deleted"

    # RPC Routes
    RPC_VALIDATE_TOKEN = "rpc.auth.validate_token"
    RPC_GET_USER_PROFILE = "rpc.auth.get_user_profile"


# =============================================================================
# Exchange Names
# =============================================================================


class Exchanges:
    """Centralized exchange name definitions"""

    AUTH_EVENTS = "auth.events"
    REVIEWS_EVENTS = "reviews.events"
    RPC_REQUESTS = "rpc.requests"


# =============================================================================
# Queue Names
# =============================================================================


class Queues:
    """Centralized queue name definitions"""

    # Auth Service Queues
    AUTH_RPC_QUEUE = "auth.rpc"

    # Reviews Service Queues
    REVIEWS_USER_EVENTS = "reviews.user_events"
    REVIEWS_RPC_RESPONSES = "reviews.rpc_responses"
