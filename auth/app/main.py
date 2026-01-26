from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import auth
from .services.eventpublisher import EventPublisher

event_publisher = EventPublisher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await event_publisher.connect()
    yield
    await event_publisher.close()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Authentication microservice",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/auth", tags=["Authentication"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"service": settings.app_name, "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name, "version": "1.0.0"}
