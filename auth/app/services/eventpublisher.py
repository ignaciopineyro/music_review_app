import logging

from datetime import datetime
from typing import Optional
from fastapi import Request
from shared.events import (
    UserRegisteredEvent,
    UserAuthenticatedEvent,
    TokenRevokedEvent,
    LoginMethod,
    TokenType,
    RevocationReason,
)
from shared.messaging import RabbitMQPublisher
from ..config import settings
from ..schemas import UserResponse


logger = logging.getLogger(__name__)


class EventPublisher:
    def __init__(self):
        self.publisher = RabbitMQPublisher(settings.rabbitmq_url)
        self._connected = False

    async def connect(self) -> None:
        if not self._connected:
            await self.publisher.connect()
            self._connected = True

    async def close(self) -> None:
        if self._connected:
            await self.publisher.close()
            self._connected = False

    async def publish_user_registered(self, user: UserResponse) -> None:
        event = UserRegisteredEvent(
            user_id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
        )

        try:
            await self.publisher.publish_event(
                event=event,
                exchange_name="auth.events",
                routing_key="user.registered",
            )
        except Exception as e:
            logger.error(f"Failed to publish user registered event: {e}")

    async def publish_user_authenticated(
        self, user: UserResponse, method: LoginMethod, request: Optional[Request] = None
    ) -> None:
        ip_address = None
        user_agent = None

        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        event = UserAuthenticatedEvent(
            user_id=user.id,
            username=user.username,
            login_method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            authenticated_at=datetime.utcnow(),
        )

        try:
            await self.publisher.publish_event(
                event=event,
                exchange_name="auth.events",
                routing_key="user.authenticated",
            )
        except Exception as e:
            logger.error(f"Failed to publish user authenticated event: {e}")

    async def publish_token_revoked(
        self, user_id: int, token_type: TokenType, reason: RevocationReason
    ) -> None:
        event = TokenRevokedEvent(
            user_id=user_id,
            token_type=token_type,
            reason=reason,
            revoked_at=datetime.utcnow(),
        )

        try:
            await self.publisher.publish_event(
                event=event,
                exchange_name="auth.events",
                routing_key="token.revoked",
            )
        except Exception as e:
            logger.error(f"Failed to publish token revoked event: {e}")

