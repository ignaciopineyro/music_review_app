# Development Tools

This directory contains development and testing utilities for the Music Review App microservices.

## Purpose

- **Shared development scripts** that work across all microservices
- **Integration testing tools** for testing communication between services
- **Database and messaging connectivity tests**
- **Development utilities and helpers**

## Virtual Environment

This directory has its own isolated virtual environment to avoid dependency conflicts with individual microservices.

### Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Available Tools

### test_rabbitmq.py
Tests RabbitMQ connectivity and messaging functionality:
- Connection testing
- Event publishing
- Event consuming
- Full message flow testing

```bash
# Run RabbitMQ tests
python test_rabbitmq.py
```

## Usage Guidelines

1. **Always activate the virtual environment** before running scripts:
   ```bash
   source .venv/bin/activate
   ```

2. **Add new development dependencies** to `requirements.txt`

3. **Keep scripts general-purpose** - service-specific scripts should go in their respective service directories

4. **Use this environment for**:
   - Cross-service integration testing
   - Database migration testing
   - Message broker testing
   - Development utilities

## Dependencies

See `requirements.txt` for the complete list of development dependencies.

Key components:
- **FastAPI/Uvicorn**: For endpoint testing
- **aio-pika**: RabbitMQ messaging
- **SQLModel/SQLAlchemy**: Database testing
- **pytest**: Testing framework
- **Development tools**: black, flake8, mypy