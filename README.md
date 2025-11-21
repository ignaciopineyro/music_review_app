# Music Review App

A modern REST API for managing music album reviews, built with FastAPI, SQLModel and PostgreSQL.

## Features

- Complete REST API with CRUD operations for albums
- Asynchronous operations for high concurrency
- Automatic data validation with Pydantic
- PostgreSQL for production, SQLite for testing
- Comprehensive testing with pytest
- Automatic API documentation with Swagger UI
- Database migrations with Alembic

## Technology Stack

### Backend Framework
- **FastAPI 0.121.3** - Modern, fast web framework for building APIs
- **Uvicorn 0.38.0** - ASGI server for production deployment

### Database & ORM
- **PostgreSQL** - Production database (with asyncpg driver)
- **SQLite** - Testing database (with aiosqlite driver)
- **SQLModel 0.0.27** - Modern Python SQL toolkit
- **SQLAlchemy 2.0.44** - Database toolkit and ORM
- **Alembic 1.17.2** - Database migration tool

### Testing & Development
- **pytest 9.0.1** - Testing framework
- **pytest-asyncio 0.21.1** - Async testing support
- **httpx 0.28.1** - HTTP client for testing
- **aiosqlite 0.20.0** - Async SQLite driver

### Configuration & Environment
- **python-dotenv 1.2.1** - Environment variable management
- **asyncpg 0.30.0** - PostgreSQL async driver

## Project Structure

```
music_review_app/
├── app/
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── routers/         # API endpoints
│   ├── db.py           # Database configuration
│   ├── config.py       # Application configuration
│   └── main.py         # FastAPI application entry point
├── tests/
│   ├── conftest.py     # Test configuration
│   └── test_albums.py  # Album endpoint tests
├── requirements.txt    # Python dependencies
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL (for production)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ignaciopineyro/music_review_app.git
cd music_review_app
```

2. Create and activate virtual environment:
```bash
python -m venv music_review_app
source music_review_app/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
echo "DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/music_reviews" > .env
```

5. Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at: http://localhost:8000

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

Run all tests:
```bash
pytest
```

Run tests with verbose output:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_albums.py -v
```

## Database Configuration

### Production
Create a `.env` file with PostgreSQL connection:
```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/music_reviews
```

### Development (SQLite)
```env
DATABASE_URL=sqlite+aiosqlite:///./music_reviews.db
```

## License

This project is licensed under the MIT License.
