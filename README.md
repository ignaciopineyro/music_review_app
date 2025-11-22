# Music Review App

A RESTful API built with FastAPI for managing music album reviews.

## Quick Start with Docker

### Prerequisites
- Docker
- Docker Compose

### Start Complete Application
```bash
# Start PostgreSQL + FastAPI
./start-dev.sh
```

### Database Only (Local Development)
```bash
# Start only PostgreSQL
./start-db-only.sh
```

## API Endpoints

Once the application is running, visit:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Endpoints:
- `GET /albums/` - List albums
- `POST /albums/` - Create album
- `GET /albums/{id}` - Get album by ID
- `PUT /albums/{id}` - Update album
- `DELETE /albums/{id}` - Delete album

## Database

### PostgreSQL (Production/Docker)
- **Host**: localhost:5432
- **User**: musicuser
- **Password**: musicpass
- **Database**: music_reviews

### Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Testing

```bash
# Run tests (uses SQLite in-memory)
pytest
```

## Local Development

### With Docker (Recommended)
```bash
./start-dev.sh  # Everything in containers
```

### Hybrid Development
```bash
./start-db-only.sh  # Only PostgreSQL in Docker
# In another terminal:
uvicorn app.main:app --reload  # FastAPI locally
```

## Project Structure

```
music_review_app/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── models.py        # SQLModel models
│   ├── db.py           # Database configuration
│   ├── config.py       # Environment variables
│   └── routers/
│       └── albums.py   # Album endpoints
├── tests/
│   ├── conftest.py     # Test configuration
│   └── test_albums.py  # Album tests
├── alembic/            # Database migrations
├── docker-compose.yml  # Docker configuration
├── Dockerfile         # FastAPI image
└── requirements.txt   # Python dependencies
```

## Configuration

Environment variables in `.env`:
```
DATABASE_URL=postgresql+asyncpg://musicuser:musicpass@localhost:5432/music_reviews
ALEMBIC_DATABASE_URL=postgresql://musicuser:musicpass@localhost:5432/music_reviews
```

