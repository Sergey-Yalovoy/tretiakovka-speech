from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.db.models import (
    Artwork,
    Author,
    Category,
    Style,
    Material,
    Technique,
)


class ArtworkRepository:

    @staticmethod
    def _options():
        return (
            selectinload(Artwork.authors),
            selectinload(Artwork.categories),
            selectinload(Artwork.styles),
            selectinload(Artwork.materials),
            selectinload(Artwork.techniques),
        )

    async def get(
            self,
            session: AsyncSession,
            artwork_id: int,
    ) -> Artwork | None:
        stmt = (
            select(Artwork)
            .where(Artwork.id == artwork_id)
            .options(*self._options())
        )

        result = await session.execute(stmt)

        return result.scalar_one_or_none()


@dataclass(slots=True)
class ArtworkFilter:
    q: str | None = None

    author_ids: list[int] | None = None
    category_ids: list[int] | None = None
    style_ids: list[int] | None = None
    material_ids: list[int] | None = None
    technique_ids: list[int] | None = None

    periods: list[str] | None = None


async def list(
        self,
        session: AsyncSession,
        *,
        filters: ArtworkFilter,
        page: int = 1,
        page_size: int = 20,
):
    stmt = (
        select(Artwork)
        .options(*self._options())
    )

    if filters.author_ids:
        stmt = stmt.where(
            Artwork.authors.any(
                Author.id.in_(filters.author_ids)
            )
        )

    if filters.category_ids:
        stmt = stmt.where(
            Artwork.categories.any(
                Category.id.in_(filters.category_ids)
            )
        )

    if filters.style_ids:
        stmt = stmt.where(
            Artwork.styles.any(
                Style.id.in_(filters.style_ids)
            )
        )

    if filters.material_ids:
        stmt = stmt.where(
            Artwork.materials.any(
                Material.id.in_(filters.material_ids)
            )
        )

    if filters.technique_ids:
        stmt = stmt.where(
            Artwork.techniques.any(
                Technique.id.in_(filters.technique_ids)
            )
        )

    if filters.periods:
        stmt = stmt.where(
            Artwork.period.in_(filters.periods)
        )

    from sqlalchemy import func

    if filters.q:
        query = func.plainto_tsquery(
            "russian",
            filters.q,
        )

        stmt = stmt.where(
            Artwork.search_vector.op("@@")(query)
        )

    offset = (page - 1) * page_size

    stmt = (
        stmt
        .offset(offset)
        .limit(page_size)
    )

    result = await session.execute(stmt)

    return result.scalars().unique().all()
