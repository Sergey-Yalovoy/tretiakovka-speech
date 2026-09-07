import html
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Artwork, Author, Material, Style, Technique
from app.repositories.artwork import ArtworkFilter, ArtworkRepository
from app.tretyakov.client import TretyakovClient
from app.tretyakov.schemas import (
    TretyakovGalleryDetail,
    TretyakovGalleryItem,
)

TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")


def strip_html(text: str | None) -> str:
    if not text:
        return ""

    plain = TAG_RE.sub(" ", html.unescape(text))

    plain = WHITESPACE_RE.sub(" ", plain)
    plain = re.sub(r"\s*\n\s*", "\n", plain)

    return plain.strip()


def new_strip_html(text: str | None) -> str:
    if not text:
        return ""

    text_only = nh3.clean(text, tags=set())
    return text_only.strip()


def build_tts_text(artwork: Artwork) -> str:
    parts = [
        artwork.name,
        new_strip_html(artwork.description),
        new_strip_html(artwork.facts),
    ]

    text = ". ".join(part for part in parts if part)

    return text.strip()


class ArtworkService:

    def __init__(
            self,
            repository: ArtworkRepository,
            tretyakov: TretyakovClient,
    ):
        self.repository = repository
        self.tretyakov = tretyakov

    async def get(
            self,
            session: AsyncSession,
            artwork_id: int,
    ) -> Artwork | None:
        return await self.repository.get(
            session,
            artwork_id,
        )

    async def list(
            self,
            session: AsyncSession,
            *,
            filters: ArtworkFilter,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[list[Artwork], int]:
        return await self.repository.list(
            session,
            filters=filters,
            page=page,
            page_size=page_size,
        )

    async def get_or_fetch(
            self,
            session: AsyncSession,
            artwork_id: int,
    ) -> Artwork | None:
        artwork = await self.get(session, artwork_id)

        if artwork is not None:
            return artwork

        remote = await self.tretyakov.gallery_by_id(artwork_id)

        if remote is None:
            return None

        artwork = await self.upsert_detail(session, remote)

        await session.commit()

        return artwork

    async def upsert_list_item(
            self,
            session: AsyncSession,
            item: TretyakovGalleryItem,
    ) -> Artwork:
        """Данные из gallery/get (список): стиль, период, картинки, размер."""

        artwork = await session.get(Artwork, item.id)

        if artwork is None:
            artwork = Artwork(id=item.id, name=item.name)
            session.add(artwork)

        artwork.code = item.code
        artwork.name = item.name
        artwork.period = item.period

        artwork.picture_big = list(item.picture_big or [])
        artwork.picture_thumb = list(item.picture_thumb or [])

        if item.size:
            artwork.height = item.size.height
            artwork.width = item.size.width
            artwork.depth = item.size.depth

        artwork.authors = [
            await self._author(session, author)
            for author in item.author
        ]
        artwork.styles = [
            await self._style(session, style)
            for style in item.style
        ]

        return artwork

    async def upsert_detail(
            self,
            session: AsyncSession,
            detail: TretyakovGalleryDetail,
    ) -> Artwork:
        """Данные из gallery/getById: материалы, техника, описание, год."""

        artwork = await session.get(Artwork, detail.id)

        if artwork is None:
            artwork = Artwork(id=detail.id, name=detail.name,
                              authors=[],
                              materials=[],
                              techniques=[],
                              styles=[]
                              )
            session.add(artwork)
        else:
            await session.refresh(artwork, ["authors", "materials", "techniques", "styles"])

        artwork.name = detail.name

        artwork.picture_big = (
                list(detail.picture_big) or artwork.picture_big
        )
        artwork.picture_thumb = (
                list(detail.picture_thumb) or artwork.picture_thumb
        )

        if detail.size:
            artwork.height = detail.size.height
            artwork.width = detail.size.width
            artwork.depth = detail.size.depth

        artwork.placement = detail.placement or None
        artwork.creat = detail.creat
        artwork.creat_f = detail.creat_f

        artwork.description = detail.description
        artwork.facts = detail.facts or None

        artwork.authors = [
            await self._author(session, author)
            for author in detail.author
        ]
        artwork.materials = [
            await self._material(session, material)
            for material in detail.material
        ]
        artwork.techniques = [
            await self._technique(session, technique)
            for technique in detail.technique
        ]

        return artwork

    async def _author(
            self,
            session: AsyncSession,
            source,
    ) -> Author:
        author = await session.get(Author, source.id)

        if author is None:
            author = Author(id=source.id, name=source.name)
            session.add(author)
            # flush делает объект видимым для session.get()
            # в рамках этой же сессии и страницы.
            await session.flush()

        author.name = source.name
        author.years = getattr(source, "years", None)

        return author

    async def _style(
            self,
            session: AsyncSession,
            source,
    ) -> Style:
        style = await session.get(Style, source.id)

        if style is None:
            style = Style(id=source.id, name=source.name)
            session.add(style)
            await session.flush()

        style.name = source.name

        return style

    async def _material(
            self,
            session: AsyncSession,
            source,
    ) -> Material:
        material = await session.get(Material, int(source.id))

        if material is None:
            material = Material(id=int(source.id), name=source.name)
            session.add(material)
            await session.flush()

        material.name = source.name

        return material

    async def _technique(
            self,
            session: AsyncSession,
            source,
    ) -> Technique:
        technique = await session.get(Technique, int(source.id))

        if technique is None:
            technique = Technique(id=int(source.id), name=source.name)
            session.add(technique)
            await session.flush()

        technique.name = source.name

        return technique


async def existing_artwork_ids(
        session: AsyncSession,
) -> set[int]:
    result = await session.execute(select(Artwork.id))
    return {row[0] for row in result.all()}
