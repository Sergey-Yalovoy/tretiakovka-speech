from dataclasses import dataclass

from app.config import Settings, get_settings
from app.logger import get_logger
from app.services.audio_guide import AudioGuideService
from app.tretyakov.client import TretyakovClient
from storage.local import LocalFileStorage
from storage.s3 import S3FileStorage

logger = get_logger(__name__)


@dataclass
class Runtime:
    settings: Settings
    tretyakov: TretyakovClient
    audio: AudioGuideService


_runtime: Runtime | None = None


def init_runtime(settings: Settings | None = None) -> Runtime:
    global _runtime

    if _runtime is not None:
        return _runtime

    settings = settings or get_settings()

    tretyakov = TretyakovClient(
        base_url=settings.tretyakov_base_url,
        timeout=settings.http_timeout,
    )

    if settings.storage_backend == "s3":
        storage: S3FileStorage | LocalFileStorage = S3FileStorage(
            bucket=settings.s3_bucket,
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            public_url=settings.s3_public_url,
            access_key_id=settings.s3_access_key,
            secret_access_key=settings.s3_secret_key.get_secret_value(),
        )
    else:
        storage = LocalFileStorage(
            root=settings.media_root,
        )

    audio = AudioGuideService(
        storage=storage,
        model_path=settings.tts_model_path,
        speaker=settings.tts_speaker,
        sample_rate=settings.audio_sample_rate,
    )

    _runtime = Runtime(
        settings=settings,
        tretyakov=tretyakov,
        audio=audio,
    )

    return _runtime


def get_runtime() -> Runtime:
    assert _runtime is not None, (
        "Runtime is not initialized - call init_runtime() first"
    )
    return _runtime


async def shutdown_runtime() -> None:
    global _runtime

    if _runtime is None:
        return

    await _runtime.tretyakov.aclose()
    _runtime = None

    logger.info("Runtime shut down")
