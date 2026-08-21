from fastapi import FastAPI

from app.api.artworks import router as artworks_router

app = FastAPI(
    title="Tretyakov Parser",
    version="0.1.0",
)

app.include_router(artworks_router)
