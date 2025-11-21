from fastapi import FastAPI
from contextlib import asynccontextmanager
from .routers import albums
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    print("App shutting down")


app = FastAPI(lifespan=lifespan)
app.include_router(albums.router)
