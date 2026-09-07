from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Artwork,
    Author,
    Material,
    Style,
    Technique,
)


@dataclass(slots=True)
class ArtworkFilter:
    q: str | None = None

    author_ids: list[int] = field(default_factory=list)
    style_ids: list[int] = field(default_factory=list)
    material_ids: list[int] = field(default_factory=list)
    technique_ids: list[int] = field(default_factory=list)

    periods: list[str] = field(default_factory=list)


class ArtworkRepository:

    async def get(
            self,
            session: AsyncSession,
            artwork_id: int,
    ) -> Artwork | None:
        stmt = select(Artwork).where(
            Artwork.id == artwork_id,
        )

        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    async def list(
            self,
            session: AsyncSession,
            *,
            filters: ArtworkFilter,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[list[Artwork], int]:

        stmt = select(Artwork)

        if filters.author_ids:
            stmt = stmt.where(
                Artwork.authors.any(
                    Author.id.in_(filters.author_ids),
                ),
            )

        if filters.style_ids:
            stmt = stmt.where(
                Artwork.styles.any(
                    Style.id.in_(filters.style_ids),
                ),
            )

        if filters.material_ids:
            stmt = stmt.where(
                Artwork.materials.any(
                    Material.id.in_(filters.material_ids),
                ),
            )

        if filters.technique_ids:
            stmt = stmt.where(
                Artwork.techniques.any(
                    Technique.id.in_(filters.technique_ids),
                ),
            )

        if filters.periods:
            stmt = stmt.where(
                Artwork.period.in_(filters.periods),
            )

        if filters.q:
            stmt = stmt.where(
                Artwork.search_vector.op("@@")(
                    func.plainto_tsquery(
                        "russian",
                        filters.q,
                    ),
                ),
            )

        count_stmt = select(
            func.count(),
        ).select_from(
            stmt.subquery(),
        )

        total = (
            await session.execute(count_stmt)
        ).scalar_one()

        offset = (page - 1) * page_size

        stmt = (
            stmt
            .order_by(Artwork.id)
            .offset(offset)
            .limit(page_size)
        )

        items = (
            await session.execute(stmt)
        ).scalars().all()

        return list(items), total


class DictionaryRepository:

    async def authors(
            self,
            session: AsyncSession,
    ) -> list[Author]:
        result = await session.execute(
            select(Author).order_by(Author.name),
        )
        return list(result.scalars().all())

    async def styles(
            self,
            session: AsyncSession,
    ) -> list[Style]:
        result = await session.execute(
            select(Style).order_by(Style.name),
        )
        return list(result.scalars().all())

    async def materials(
            self,
            session: AsyncSession,
    ) -> list[Material]:
        result = await session.execute(
            select(Material).order_by(Material.name),
        )
        return list(result.scalars().all())

    async def techniques(
            self,
            session: AsyncSession,
    ) -> list[Technique]:
        result = await session.execute(
            select(Technique).order_by(Technique.name),
        )
        return list(result.scalars().all())

    async def periods(
            self,
            session: AsyncSession,
    ) -> list[str]:
        result = await session.execute(
            select(Artwork.period)
            .where(Artwork.period.is_not(None))
            .distinct()
            .order_by(Artwork.period),
        )
        return [row[0] for row in result.all()]
