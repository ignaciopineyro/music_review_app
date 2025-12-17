"""
Shared utilities and components for Music Review App microservices.
"""

from .messaging import (
    MessageBroker,
    EventPublisher,
    EventConsumer,
    EventHandler,
    RPCClient,
    RPCServer,
    EventBase,
)

from .events import (
    # Auth Events
    UserRegisteredEvent,
    UserLoginEvent,
    UserLogoutEvent,
    TokenRevokedEvent,
    UserProfileUpdatedEvent,
    # Reviews Events
    AlbumCreatedEvent,
    AlbumUpdatedEvent,
    AlbumDeletedEvent,
    ReviewCreatedEvent,
    ReviewUpdatedEvent,
    ReviewDeletedEvent,
    # RPC Models
    ValidateTokenRequest,
    ValidateTokenResponse,
    GetUserProfileRequest,
    GetUserProfileResponse,
    # Constants
    RoutingKeys,
    Exchanges,
    Queues,
    EVENT_REGISTRY,
)

__version__ = "1.0.0"
__all__ = [
    # Messaging
    "MessageBroker",
    "EventPublisher",
    "EventConsumer",
    "EventHandler",
    "RPCClient",
    "RPCServer",
    "EventBase",
    # Events
    "UserRegisteredEvent",
    "UserLoginEvent",
    "UserLogoutEvent",
    "TokenRevokedEvent",
    "UserProfileUpdatedEvent",
    "AlbumCreatedEvent",
    "AlbumUpdatedEvent",
    "AlbumDeletedEvent",
    "ReviewCreatedEvent",
    "ReviewUpdatedEvent",
    "ReviewDeletedEvent",
    # RPC
    "ValidateTokenRequest",
    "ValidateTokenResponse",
    "GetUserProfileRequest",
    "GetUserProfileResponse",
    # Constants
    "RoutingKeys",
    "Exchanges",
    "Queues",
    "EVENT_REGISTRY",
]
