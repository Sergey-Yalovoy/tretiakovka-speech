import tempfile
from pathlib import Path
from uuid import uuid4

from audio.models import StoredAudio
from storage.base import FileStorage
from tts.silero_tts import SileroTTS


class AudioService:

    def __init__(
            self,
            tts: SileroTTS,
            storage: FileStorage,
    ):
        self.tts = tts
        self.storage = storage

    def generate(
            self,
            text: str,
            speaker: str,
            file_id: str | None = None,
            sample_rate: int = 48_000
    ) -> StoredAudio:
        if not file_id:
            file_id = str(uuid4())

        # Сохраняем сразу в .ogg
        key = f"audio/{speaker}/{file_id}-{speaker}.ogg"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "audio.ogg"

            # Silero сама всё обработает в RAM и спасет сразу в Opus OGG!
            self.tts.synthesize_to_file(
                text=text,
                output_path=temp_path,
                sample_rate=sample_rate,
            )

            stored = self.storage.save(
                source=temp_path,
                key=key,
                content_type="audio/ogg",
            )

        return StoredAudio(
            key=stored.key,
            file_id=file_id,
            content_type=stored.content_type,
        )
