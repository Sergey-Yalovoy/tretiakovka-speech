import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.artwork import ArtworkRepository
from app.schemas.artwork import (
    ArtworkResponse,
    ParseArtworkRequest,
)
from app.services.artwork import ArtworkService
from app.tretyakov.client import TretyakovClient

router = APIRouter(
    prefix="/api/v1/artworks",
    tags=["artworks"],
)


def get_service() -> ArtworkService:
    return ArtworkService(
        repository=ArtworkRepository(),
        tretyakov=TretyakovClient(),
    )


ARTWORK_URL_RE = re.compile(
    r"^https?://my\.tretyakov\.ru/app/masterpiece/(?P<id>\d+)/?$"
)


@router.get(
    "/{artwork_id}",
    response_model=ArtworkResponse,
)
async def get_artwork(
        artwork_id: int,
        session: AsyncSession = Depends(get_session),
):
    repository = ArtworkRepository()

    artwork = await repository.get(
        session,
        artwork_id,
    )

    if artwork is None:
        raise HTTPException(
            status_code=404,
            detail="Artwork not found",
        )

    return artwork


@router.post(
    "/parse",
    response_model=ArtworkResponse,
)
async def parse_artwork(
        payload: ParseArtworkRequest,
        session: AsyncSession = Depends(get_session),
):
    match = ARTWORK_URL_RE.match(payload.url)

    if not match:
        raise HTTPException(
            status_code=422,
            detail="Invalid Tretyakov artwork URL",
        )

    artwork_id = int(match.group("id"))

    client = TretyakovClient()

    try:
        service = ArtworkService(
            repository=ArtworkRepository(),
            tretyakov=client,
        )

        artwork = await service.get_or_fetch(
            session,
            artwork_id,
        )

        if artwork is None:
            raise HTTPException(
                status_code=404,
                detail="Artwork not found in Tretyakov API",
            )

        return artwork

    finally:
        await client.close()
