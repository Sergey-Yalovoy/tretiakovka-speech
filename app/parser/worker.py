"""Точка входа автоматического парсера: python -m app.parser.worker"""

import asyncio

from app.config import get_settings
from app.db.session import session_maker
from app.deps import shutdown_runtime
from app.logger import get_logger
from app.parser.sync import GallerySyncService
from app.tretyakov.client import TretyakovClient

logger = get_logger("app.parser.worker")


async def main() -> None:
    settings = get_settings()

    client = TretyakovClient(
        base_url=settings.tretyakov_base_url,
        timeout=settings.http_timeout,
    )

    sync = GallerySyncService(
        tretyakov=client,
        session_maker=session_maker,
        settings=settings,
    )

    logger.info(
        "Parser worker started: interval=%ss page_size=%s startup_sync=%s",
        settings.sync_interval_seconds,
        settings.sync_page_size,
        settings.sync_on_startup,
    )

    first_run = True

    try:
        while True:
            if settings.sync_on_startup or not first_run:
                started_at = asyncio.get_event_loop().time()

                try:
                    stats = await sync.sync_catalog()
                    logger.info("Sync finished: %s", stats.summary())
                except Exception:
                    logger.exception("Sync failed")

                elapsed = asyncio.get_event_loop().time() - started_at
                logger.info("Sync took %.1fs", elapsed)

            first_run = False

            logger.info(
                "Sleeping for %s seconds",
                settings.sync_interval_seconds,
            )

            await asyncio.sleep(settings.sync_interval_seconds)
    finally:
        await client.aclose()
        await shutdown_runtime()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Parser worker stopped")
