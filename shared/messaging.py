import logging
import aio_pika

from typing import Optional
from aio_pika import Message, DeliveryMode, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractChannel
from .events import BaseEvent


logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractChannel] = None

    async def connect(self) -> None:
        try:
            self.connection = await aio_pika.connect_robust(self.connection_url)
            self.channel = await self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def close(self) -> None:
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("Disconnected from RabbitMQ")

    async def declare_exchange(
        self, name: str, exchange_type: ExchangeType = ExchangeType.TOPIC
    ) -> None:
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ")

        await self.channel.declare_exchange(name, exchange_type, durable=True)
        logger.info(f"Declared exchange '{name}' of type {exchange_type}")

    async def publish_event(
        self,
        event: BaseEvent,
        exchange_name: str,
        routing_key: str,
        headers: Optional[dict] = None,
    ) -> None:
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ")

        await self.declare_exchange(exchange_name)

        message_body = event.model_dump_json()
        message_headers = headers or {}

        event_data = event.model_dump()
        event_type = event_data.get("event_type", type(event).__name__)

        message_headers.update(
            {
                "event_type": event_type,
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
            }
        )

        message = Message(
            message_body.encode(),
            headers=message_headers,
            delivery_mode=DeliveryMode.PERSISTENT,
        )

        exchange = await self.channel.get_exchange(exchange_name)
        await exchange.publish(message, routing_key=routing_key)

        logger.info(f"Published event {event_type} to {exchange_name}/{routing_key}")
