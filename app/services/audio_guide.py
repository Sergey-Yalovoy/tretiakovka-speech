import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Artwork
from app.logger import get_logger
from audio.service import AudioService
from storage.base import FileStorage
from tts.silero_tts import SileroTTS

from .artwork import build_tts_text

logger = get_logger(__name__)


class AudioGuideService:

    def __init__(
            self,
            storage: FileStorage,
            model_path: str = "models/v5_5_ru.pt",
            speaker: str = "baya",
            sample_rate: int = 48_000,
    ):
        self.storage = storage
        self.sample_rate = sample_rate
        self.speaker = speaker
        self.model_path = model_path

        self._tts: SileroTTS | None = None
        self._tts_lock = asyncio.Lock()
        self._artwork_locks: dict[int, asyncio.Lock] = {}

    @property
    def loaded(self) -> bool:
        return self._tts is not None

    async def _ensure_tts(self, speaker: str | None = None) -> SileroTTS:
        if self._tts is not None:
            return self._tts

        async with self._tts_lock:
            if self._tts is None:
                logger.info("Loading Silero TTS model...")

                self._tts = await asyncio.to_thread(
                    SileroTTS,
                    model_path=self.model_path,
                    speaker=speaker if speaker is not None else self.speaker,
                    max_chunk_size=500
                )

                logger.info("Silero TTS model loaded")

        return self._tts

    def _lock_for(self, artwork_id: int) -> asyncio.Lock:
        if artwork_id not in self._artwork_locks:
            self._artwork_locks[artwork_id] = asyncio.Lock()

        return self._artwork_locks[artwork_id]

    def get_audio_key(self, artwork: Artwork, speaker: str) -> str | None:
        return f"audio/{speaker}/{artwork.audio_key}-{speaker}.ogg"

    async def ensure_audio(
            self,
            session: AsyncSession,
            artwork: Artwork,
            speaker: str | None = None
    ) -> str | None:
        """Возвращает ключ готового аудио или None, если озвучивать нечего.

        Генерирует один раз, кеширует в хранилище и в БД.
        """

        speaker = speaker if speaker is not None else self.speaker

        text = build_tts_text(artwork)

        if not text:
            return None

        key = self.get_audio_key(artwork, speaker)

        if key and await self._exists(key):
            return key

        async with self._lock_for(artwork.id):
            self._tts = None
            tts = await self._ensure_tts(speaker=speaker)

            audio_service = AudioService(
                tts=tts,
                storage=self.storage,
            )

            logger.info(
                "Generating audio for artwork %s (%s chars)",
                artwork.id,
                len(text),
            )

            stored = await asyncio.to_thread(
                lambda: audio_service.generate(
                    text=text,
                    sample_rate=self.sample_rate,
                    speaker=speaker,
                    file_id=artwork.audio_key
                ),
            )
            if artwork.audio_key != stored.file_id:
                artwork.audio_key = stored.file_id
                artwork.audio_generated_at = datetime.now(timezone.utc)
                await session.commit()

            logger.info("Audio ready: %s", stored.key)

            return stored.key

    async def _exists(self, key: str) -> bool:
        try:
            await asyncio.to_thread(self.storage.stat, key)
            return True
        except Exception:
            return False

    def url(self, key: str) -> str:
        return self.storage.get_url(key)
