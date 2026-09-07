import asyncio
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.db.models import Artwork
from app.logger import get_logger
from app.repositories.artwork import ArtworkRepository
from app.services.artwork import ArtworkService
from app.tretyakov.client import TretyakovClient

logger = get_logger(__name__)


@dataclass
class SyncStats:
    pages: int = 0
    list_items: int = 0
    details_fetched: int = 0
    details_missing: int = 0
    errors: int = 0

    def summary(self) -> str:
        return (
            f"pages={self.pages} "
            f"list_items={self.list_items} "
            f"details_fetched={self.details_fetched} "
            f"details_missing={self.details_missing} "
            f"errors={self.errors}"
        )


class GallerySyncService:
    """Полная синхронизация каталога my.tretyakov.ru с базой.

    Этап 1: постраничный обход gallery/get (по sync_page_size элементов),
             апсерт списка (имя, период, стили, авторы, картинки).
    Этап 2: gallery/getById для картин без описания (материалы, техника,
             год, описание, факты) с ограничением параллелизма.
    """

    def __init__(
            self,
            tretyakov: TretyakovClient,
            session_maker: async_sessionmaker[AsyncSession],
            settings: Settings,
    ):
        self.tretyakov = tretyakov
        self.session_maker = session_maker
        self.settings = settings

    def _service(self) -> ArtworkService:
        return ArtworkService(
            repository=ArtworkRepository(),
            tretyakov=self.tretyakov,
        )

    async def sync_catalog(self) -> SyncStats:
        stats = SyncStats()

        await self._sync_list(stats)
        await self._sync_details(stats)

        return stats

    async def _sync_list(self, stats: SyncStats) -> None:
        service = self._service()

        page = 1

        while True:
            try:
                response = await self.tretyakov.gallery(
                    page=page,
                    page_size=self.settings.sync_page_size,
                )
            except Exception:
                stats.errors += 1
                logger.exception("gallery/get page %s failed", page)
                break

            async with self.session_maker() as session:
                try:
                    for item in response.items:
                        await service.upsert_list_item(session, item)

                    await session.commit()
                except Exception:
                    stats.errors += 1
                    logger.exception("upsert of page %s failed", page)
                    break

            stats.pages += 1
            stats.list_items += len(response.items)

            logger.info(
                "List sync: page %s/%s (%s items)",
                page,
                response.page_count,
                len(response.items),
            )

            max_pages = self.settings.sync_max_pages

            if page >= response.page_count:
                break

            if max_pages is not None and page >= max_pages:
                logger.info("Reached SYNC_MAX_PAGES=%s, stopping", max_pages)
                break

            page += 1

            await asyncio.sleep(self.settings.sync_request_delay)

    async def _sync_details(self, stats: SyncStats) -> None:
        async with self.session_maker() as session:
            result = await session.execute(
                select(Artwork.id).where(
                    Artwork.description.is_(None),
                ),
            )
            artwork_ids = [row[0] for row in result.all()]

        if not artwork_ids:
            logger.info("Detail sync: nothing to fetch")
            return

        logger.info(
            "Detail sync: %s artworks to fetch",
            len(artwork_ids),
        )

        service = self._service()

        semaphore = asyncio.Semaphore(
            self.settings.sync_detail_concurrency,
        )

        async def fetch(artwork_id: int) -> None:
            async with semaphore:
                try:
                    detail = await self.tretyakov.gallery_by_id(artwork_id)
                except Exception:
                    stats.errors += 1
                    logger.exception(
                        "getById %s failed",
                        artwork_id,
                    )
                    return

                if detail is None:
                    stats.details_missing += 1
                    return

                # Параллельные задачи могут вставлять один и тот же
                # справочник одновременно; при гонке повторяем один раз.
                for attempt in (1, 2):
                    try:
                        async with self.session_maker() as session:
                            await service.upsert_detail(session, detail)
                            await session.commit()
                    except Exception:
                        if attempt == 2:
                            stats.errors += 1
                            logger.exception(
                                "detail upsert %s failed",
                                artwork_id,
                            )
                            return

                        await asyncio.sleep(0.5 * attempt)
                        continue
                    break

                stats.details_fetched += 1

                if stats.details_fetched % 100 == 0:
                    logger.info(
                        "Detail sync progress: %s/%s",
                        stats.details_fetched,
                        len(artwork_ids),
                    )

                await asyncio.sleep(
                    self.settings.sync_request_delay,
                )

        await asyncio.gather(
            *(fetch(artwork_id) for artwork_id in artwork_ids),
        )
