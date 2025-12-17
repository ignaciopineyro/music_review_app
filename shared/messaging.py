"""
Shared messaging module for RabbitMQ communication between microservices.
Provides base classes and utilities for publishing and consuming events.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Callable, Optional, Union
from abc import ABC, abstractmethod
from datetime import datetime

import aio_pika
from aio_pika import Message, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel, AbstractQueue
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class EventBase(BaseModel):
    """Base class for all events"""

    event_id: str
    timestamp: datetime
    service_name: str
    event_type: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class MessageBroker:
    """RabbitMQ message broker client"""

    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.exchanges: Dict[str, aio_pika.Exchange] = {}

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url, loop=asyncio.get_event_loop()
            )
            self.channel = await self.connection.channel()

            # Set QoS for fair dispatch
            await self.channel.set_qos(prefetch_count=10)

            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def declare_exchange(
        self, name: str, exchange_type: ExchangeType = ExchangeType.TOPIC
    ):
        """Declare an exchange"""
        if name not in self.exchanges:
            exchange = await self.channel.declare_exchange(
                name=name, type=exchange_type, durable=True
            )
            self.exchanges[name] = exchange
            logger.info(f"Declared exchange: {name}")
        return self.exchanges[name]

    async def declare_queue(self, name: str, durable: bool = True) -> AbstractQueue:
        """Declare a queue"""
        queue = await self.channel.declare_queue(name=name, durable=durable)
        logger.info(f"Declared queue: {name}")
        return queue

    async def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str):
        """Bind queue to exchange with routing key"""
        queue = await self.declare_queue(queue_name)
        exchange = await self.declare_exchange(exchange_name)

        await queue.bind(exchange, routing_key=routing_key)
        logger.info(
            f"Bound queue '{queue_name}' to exchange '{exchange_name}' with routing key '{routing_key}'"
        )
        return queue


class EventPublisher:
    """Publisher for sending events to RabbitMQ"""

    def __init__(self, broker: MessageBroker, service_name: str):
        self.broker = broker
        self.service_name = service_name

    async def publish_event(
        self,
        event: EventBase,
        exchange_name: str,
        routing_key: str,
        headers: Optional[Dict[str, Any]] = None,
    ):
        """Publish an event to RabbitMQ"""
        try:
            exchange = await self.broker.declare_exchange(exchange_name)

            # Serialize event to JSON
            event_data = event.json()

            # Create message
            message = Message(
                body=event_data.encode(),
                content_type="application/json",
                headers=headers or {},
                message_id=event.event_id,
                timestamp=event.timestamp,
            )

            # Publish message
            await exchange.publish(message=message, routing_key=routing_key)

            logger.info(
                f"Published event {event.event_type} to {exchange_name} with routing key {routing_key}"
            )

        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise


class EventHandler(ABC):
    """Abstract base class for event handlers"""

    @abstractmethod
    async def handle(
        self, event_data: Dict[str, Any], message: aio_pika.IncomingMessage
    ):
        """Handle incoming event"""
        pass


class EventConsumer:
    """Consumer for receiving events from RabbitMQ"""

    def __init__(self, broker: MessageBroker, service_name: str):
        self.broker = broker
        self.service_name = service_name
        self.handlers: Dict[str, EventHandler] = {}

    def register_handler(self, event_type: str, handler: EventHandler):
        """Register an event handler for a specific event type"""
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    async def start_consuming(self, queue_name: str):
        """Start consuming messages from a queue"""
        queue = await self.broker.declare_queue(queue_name)

        async def message_handler(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    # Parse message body
                    event_data = json.loads(message.body.decode())
                    event_type = event_data.get("event_type")

                    # Find and execute handler
                    if event_type in self.handlers:
                        await self.handlers[event_type].handle(event_data, message)
                        logger.info(f"Handled event {event_type}")
                    else:
                        logger.warning(
                            f"No handler registered for event type: {event_type}"
                        )

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message body: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    raise

        # Start consuming
        await queue.consume(message_handler)
        logger.info(f"Started consuming from queue: {queue_name}")


class RPCClient:
    """RPC client for request-response pattern"""

    def __init__(self, broker: MessageBroker):
        self.broker = broker
        self.response_queue = None
        self.pending_responses: Dict[str, asyncio.Future] = {}

    async def setup(self):
        """Setup RPC client"""
        # Declare exclusive response queue
        self.response_queue = await self.broker.channel.declare_queue(exclusive=True)

        # Start consuming responses
        await self.response_queue.consume(self._handle_response)

    async def _handle_response(self, message: aio_pika.IncomingMessage):
        """Handle RPC response"""
        async with message.process():
            correlation_id = message.correlation_id
            if correlation_id in self.pending_responses:
                future = self.pending_responses.pop(correlation_id)
                try:
                    response_data = json.loads(message.body.decode())
                    future.set_result(response_data)
                except json.JSONDecodeError as e:
                    future.set_exception(e)

    async def call(
        self,
        exchange_name: str,
        routing_key: str,
        request_data: Dict[str, Any],
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Make RPC call"""
        exchange = await self.broker.declare_exchange(exchange_name)

        # Generate correlation ID
        correlation_id = f"{self.broker.channel.number}_{len(self.pending_responses)}"

        # Create future for response
        response_future = asyncio.Future()
        self.pending_responses[correlation_id] = response_future

        # Create request message
        message = Message(
            body=json.dumps(request_data).encode(),
            content_type="application/json",
            correlation_id=correlation_id,
            reply_to=self.response_queue.name,
        )

        # Send request
        await exchange.publish(message, routing_key=routing_key)

        # Wait for response with timeout
        try:
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            self.pending_responses.pop(correlation_id, None)
            raise TimeoutError(f"RPC call timeout after {timeout}s")


class RPCServer:
    """RPC server for handling request-response pattern"""

    def __init__(self, broker: MessageBroker):
        self.broker = broker
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, method_name: str, handler: Callable):
        """Register RPC method handler"""
        self.handlers[method_name] = handler
        logger.info(f"Registered RPC handler: {method_name}")

    async def start_server(self, queue_name: str):
        """Start RPC server"""
        queue = await self.broker.declare_queue(queue_name)

        async def request_handler(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    # Parse request
                    request_data = json.loads(message.body.decode())
                    method = request_data.get("method")
                    params = request_data.get("params", {})

                    # Execute handler
                    if method in self.handlers:
                        result = await self.handlers[method](**params)
                        response_data = {"result": result, "error": None}
                    else:
                        response_data = {
                            "result": None,
                            "error": f"Method not found: {method}",
                        }

                    # Send response
                    if message.reply_to:
                        response_message = Message(
                            body=json.dumps(response_data).encode(),
                            content_type="application/json",
                            correlation_id=message.correlation_id,
                        )

                        await self.broker.channel.default_exchange.publish(
                            message=response_message, routing_key=message.reply_to
                        )

                except Exception as e:
                    logger.error(f"RPC handler error: {e}")
                    if message.reply_to:
                        error_response = Message(
                            body=json.dumps({"result": None, "error": str(e)}).encode(),
                            content_type="application/json",
                            correlation_id=message.correlation_id,
                        )

                        await self.broker.channel.default_exchange.publish(
                            message=error_response, routing_key=message.reply_to
                        )

        await queue.consume(request_handler)
        logger.info(f"Started RPC server on queue: {queue_name}")
