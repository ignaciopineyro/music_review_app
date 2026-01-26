#!/usr/bin/env python3
"""
Test script to verify RabbitMQ connectivity and messaging functionality.
"""
import asyncio
import os
import sys
import logging
from datetime import datetime

# Add parent directory to path for importing shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import (
    MessageBroker, 
    EventPublisher, 
    EventConsumer,
    EventHandler,
    UserRegisteredEvent,
    AlbumCreatedEvent,
    RoutingKeys,
    Exchanges,
    Queues
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEventHandler(EventHandler):
    """Test event handler for receiving events"""
    
    async def handle(self, event_data: dict, message):
        """Handle test events"""
        event_type = event_data.get('event_type')
        logger.info(f"Received event: {event_type}")
        logger.info(f"Event data: {event_data}")


async def test_rabbitmq_connection():
    """Test basic RabbitMQ connection"""
    logger.info("Testing RabbitMQ connection...")
    
    # RabbitMQ URL (adjust if different)
    rabbitmq_url = "amqp://admin:admin123@localhost:5672/"
    
    try:
        broker = MessageBroker(rabbitmq_url)
        await broker.connect()
        
        # Test exchange and queue creation
        await broker.declare_exchange(Exchanges.AUTH_EVENTS)
        await broker.declare_exchange(Exchanges.REVIEWS_EVENTS)
        await broker.declare_queue("test_queue")
        
        logger.info("✅ RabbitMQ connection successful!")
        await broker.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ RabbitMQ connection failed: {e}")
        return False


async def test_event_publishing():
    """Test event publishing"""
    logger.info("Testing event publishing...")
    
    rabbitmq_url = "amqp://admin:admin123@localhost:5672/"
    
    try:
        broker = MessageBroker(rabbitmq_url)
        await broker.connect()
        
        publisher = EventPublisher(broker, "test-service")
        
        # Create test events
        user_event = UserRegisteredEvent(
            user_id="test-user-123",
            email="test@example.com",
            username="testuser"
        )
        
        album_event = AlbumCreatedEvent(
            album_id="test-album-123",
            title="Test Album",
            artist="Test Artist", 
            year=2023,
            created_by_user_id="test-user-123"
        )
        
        # Publish events
        await publisher.publish_event(
            user_event, 
            Exchanges.AUTH_EVENTS, 
            RoutingKeys.USER_REGISTERED
        )
        
        await publisher.publish_event(
            album_event,
            Exchanges.REVIEWS_EVENTS,
            RoutingKeys.ALBUM_CREATED
        )
        
        logger.info("✅ Events published successfully!")
        await broker.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Event publishing failed: {e}")
        return False


async def test_event_consuming():
    """Test event consuming"""
    logger.info("Testing event consuming...")
    
    rabbitmq_url = "amqp://admin:admin123@localhost:5672/"
    
    try:
        broker = MessageBroker(rabbitmq_url)
        await broker.connect()
        
        # Setup consumer
        consumer = EventConsumer(broker, "test-consumer")
        handler = TestEventHandler()
        
        # Register handlers
        consumer.register_handler("user.registered", handler)
        consumer.register_handler("album.created", handler)
        
        # Create and bind queues
        await broker.bind_queue(
            "test_user_events",
            Exchanges.AUTH_EVENTS,
            RoutingKeys.USER_REGISTERED
        )
        
        await broker.bind_queue(
            "test_album_events", 
            Exchanges.REVIEWS_EVENTS,
            RoutingKeys.ALBUM_CREATED
        )
        
        logger.info("✅ Event consumer setup successful!")
        await broker.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Event consuming setup failed: {e}")
        return False


async def test_full_message_flow():
    """Test complete publish-consume flow"""
    logger.info("Testing complete message flow...")
    
    rabbitmq_url = "amqp://admin:admin123@localhost:5672/"
    
    publisher_broker = None
    consumer_broker = None
    
    try:
        # Setup publisher
        publisher_broker = MessageBroker(rabbitmq_url)
        await publisher_broker.connect()
        publisher = EventPublisher(publisher_broker, "test-publisher")
        
        # Setup consumer  
        consumer_broker = MessageBroker(rabbitmq_url)
        await consumer_broker.connect()
        consumer = EventConsumer(consumer_broker, "test-consumer")
        handler = TestEventHandler()
        consumer.register_handler("user.registered", handler)
        
        # Setup queue
        test_queue = "test_flow_queue"
        await consumer_broker.bind_queue(
            test_queue,
            Exchanges.AUTH_EVENTS,
            RoutingKeys.USER_REGISTERED
        )
        
        # Start consuming (this runs in background)
        await consumer.start_consuming(test_queue)
        
        # Give consumer a moment to start
        await asyncio.sleep(1)
        
        # Publish test event
        test_event = UserRegisteredEvent(
            user_id="flow-test-user",
            email="flowtest@example.com", 
            username="flowtest"
        )
        
        await publisher.publish_event(
            test_event,
            Exchanges.AUTH_EVENTS,
            RoutingKeys.USER_REGISTERED
        )
        
        # Wait for message to be processed
        await asyncio.sleep(2)
        
        logger.info("✅ Full message flow test completed!")
        
    except Exception as e:
        logger.error(f"❌ Full message flow test failed: {e}")
        return False
    
    finally:
        if publisher_broker:
            await publisher_broker.disconnect()
        if consumer_broker:
            await consumer_broker.disconnect()
    
    return True


async def run_all_tests():
    """Run all RabbitMQ tests"""
    logger.info("🚀 Starting RabbitMQ connectivity tests...")
    
    tests = [
        ("Connection Test", test_rabbitmq_connection),
        ("Event Publishing Test", test_event_publishing),
        ("Event Consuming Setup Test", test_event_consuming),
        ("Full Message Flow Test", test_full_message_flow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Print results summary
    logger.info("\n" + "="*50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! RabbitMQ is working correctly.")
    else:
        logger.warning("⚠️  Some tests failed. Check RabbitMQ configuration.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_all_tests())