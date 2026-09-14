from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis_fastapi import FastAPIRedis, RedisSettings
from starlette.middleware.cors import CORSMiddleware

from app.api.artworks import router as artworks_router
from app.api.filters import router as filters_router
from app.config import get_settings
from app.deps import init_runtime, shutdown_runtime
from app.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime = init_runtime()
    logger.info("Application started")

    try:
        yield
    finally:
        await shutdown_runtime()

    del runtime


app = FastAPI(
    title="Tretyakov Speech API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
settings = get_settings()
FastAPIRedis(app).lifespan().caching()

app.include_router(artworks_router)
app.include_router(filters_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
