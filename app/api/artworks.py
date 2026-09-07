import asyncio
import re
from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.deps import get_runtime
from app.repositories.artwork import ArtworkFilter, ArtworkRepository
from app.schemas.artwork import (
    ArtworkDetailResponse,
    ArtworkListItemResponse,
    ArtworkListResponse,
    FindArtworkRequest,
    MaterialResponse,
    TechniqueResponse,
)
from app.services.artwork import ArtworkService, build_tts_text
from app.services.audio_guide import AudioGuideService

router = APIRouter(
    prefix="/api/v1/artworks",
    tags=["artworks"],
)

ARTWORK_URL_RE = re.compile(
    r"^https?://my\.tretyakov\.ru/app/masterpiece/(?P<id>\d+)/?$"
)

RANGE_RE = re.compile(
    r"^bytes=(?P<start>\d*)-(?P<end>\d*)$"
)


def _service() -> ArtworkService:
    runtime = get_runtime()

    return ArtworkService(
        repository=ArtworkRepository(),
        tretyakov=runtime.tretyakov,
    )


def _audio() -> AudioGuideService:
    return get_runtime().audio


def _list_item(
        artwork,
        audio: AudioGuideService,
) -> ArtworkListItemResponse:
    payload = ArtworkListItemResponse.model_validate(artwork).model_dump()

    if artwork.audio_key:
        payload["has_audio"] = True
    else:
        payload["has_audio"] = False

    return ArtworkListItemResponse(**payload)


def _detail_item(
        artwork,
        audio: AudioGuideService,
) -> ArtworkDetailResponse:
    base = _list_item(artwork, audio).model_dump()

    base.update(
        placement=artwork.placement,
        materials=[
            MaterialResponse(id=m.id, name=m.name)
            for m in artwork.materials
        ],
        techniques=[
            TechniqueResponse(id=t.id, name=t.name)
            for t in artwork.techniques
        ],
        facts=artwork.facts,
        description=artwork.description,
    )

    return ArtworkDetailResponse(**base)


@router.get(
    "",
    response_model=ArtworkListResponse,
    summary="Список картин с фильтрами",
)
async def list_artworks(
        session: Annotated[AsyncSession, Depends(get_session)],
        q: str | None = Query(default=None, description="Полнотекстовый поиск"),
        author_id: list[int] = Query(default=[], alias="author_id"),
        style_id: list[int] = Query(default=[], alias="style_id"),
        material_id: list[int] = Query(default=[], alias="material_id"),
        technique_id: list[int] = Query(default=[], alias="technique_id"),
        period: list[str] = Query(default=[]),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
):
    service = _service()

    items, total = await service.list(
        session,
        filters=ArtworkFilter(
            q=q,
            author_ids=author_id,
            style_ids=style_id,
            material_ids=material_id,
            technique_ids=technique_id,
            periods=period,
        ),
        page=page,
        page_size=page_size,
    )

    audio = _audio()

    return ArtworkListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_list_item(item, audio) for item in items],
    )


async def _get_artwork_or_404(
        session: AsyncSession,
        artwork_id: int,
):
    service = _service()

    artwork = await service.get(session, artwork_id)

    if artwork is None:
        raise HTTPException(
            status_code=404,
            detail="Artwork not found",
        )

    return artwork


@router.get(
    "/{artwork_id}",
    response_model=ArtworkDetailResponse,
    summary="Детальная информация о картине",
)
async def get_artwork(
        artwork_id: int,
        session: Annotated[AsyncSession, Depends(get_session)],
        with_audio: bool = Query(
            default=False,
            description="Сгенерировать озвучку, если её ещё нет",
        ),
):
    artwork = await _get_artwork_or_404(session, artwork_id)

    audio = _audio()

    if with_audio and artwork.audio_key is None:
        await audio.ensure_audio(session, artwork)

    return _detail_item(artwork, audio)


@router.post(
    "/find",
    response_model=ArtworkDetailResponse,
    summary="Найти картину по URL my.tretyakov.ru (сначала БД, затем парсинг)",
)
async def find_artwork(
        payload: FindArtworkRequest,
        session: Annotated[AsyncSession, Depends(get_session)],
        with_audio: bool = Query(default=False),
        voice: Literal['aidar', 'baya', 'kseniya', 'xenia', 'eugene'] = Query(default='baya'),
):
    match = ARTWORK_URL_RE.match(payload.url)

    if not match:
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid Tretyakov artwork URL, "
                "expected https://my.tretyakov.ru/app/masterpiece/<id>"
            ),
        )

    artwork_id = int(match.group("id"))

    service = _service()

    artwork = await service.get_or_fetch(session, artwork_id)

    if artwork is None:
        raise HTTPException(
            status_code=404,
            detail="Artwork not found in Tretyakov API",
        )

    audio = _audio()

    if with_audio and artwork.audio_key is None:
        await audio.ensure_audio(session, artwork, speaker=voice)

    return _detail_item(artwork, audio)


def _parse_range(
        range_header: str | None,
        size: int,
) -> tuple[int, int | None, int]:
    """Возвращает (start, end|None, status_code)."""

    if not range_header:
        return 0, None, 200

    match = RANGE_RE.match(range_header.strip())

    if not match:
        raise HTTPException(
            status_code=416,
            detail="Invalid Range header",
        )

    start_raw = match.group("start")
    end_raw = match.group("end")

    if start_raw == "" and end_raw == "":
        raise HTTPException(
            status_code=416,
            detail="Invalid Range header",
        )

    # suffix form: bytes=-500 — последние 500 байт
    if start_raw == "":
        length = min(int(end_raw), size)
        return size - length, size - 1, 206

    start = int(start_raw)

    if start >= size:
        raise HTTPException(
            status_code=416,
            detail="Requested range not satisfiable",
        )

    end = int(end_raw) if end_raw else None

    if end is not None and end >= size:
        end = size - 1

    return start, end, 206


@router.get(
    "/{artwork_id}/audio",
    summary="Стриминг озвучки картины (генерируется при первом запросе)",
    response_class=StreamingResponse,
)
async def stream_artwork_audio(
        artwork_id: int,
        session: Annotated[AsyncSession, Depends(get_session)],
        range: Annotated[str | None, Header()] = None,
        voice: Literal['aidar', 'baya', 'kseniya', 'xenia', 'eugene'] = 'baya',
):
    artwork = await _get_artwork_or_404(session, artwork_id)

    if build_tts_text(artwork) == "":
        raise HTTPException(
            status_code=404,
            detail="Artwork has no text to narrate",
        )

    audio = _audio()

    key = await audio.ensure_audio(session, artwork, voice)

    if key is None:
        raise HTTPException(
            status_code=404,
            detail="Audio is not available for this artwork",
        )

    try:
        meta = await _stat(audio, key)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Audio storage is unavailable",
        )

    start, end, status = _parse_range(range, meta.size)

    storage = audio.storage

    def iterator():
        yield from storage.stream(key=key, start=start, end=end)

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(meta.size - start),
    }

    if status == 206:
        actual_end = end if end is not None else meta.size - 1
        headers["Content-Range"] = (
            f"bytes {start}-{actual_end}/{meta.size}"
        )
        headers["Content-Length"] = str(actual_end - start + 1)

    return StreamingResponse(
        iterator(),
        status_code=status,
        media_type="audio/wav",
        headers=headers,
    )


async def _stat(audio: AudioGuideService, key: str):
    return await asyncio.to_thread(audio.storage.stat, key)
