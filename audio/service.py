import tempfile
from pathlib import Path
from uuid import uuid4

from storage.base import FileStorage
from tts.silero_tts import SileroTTS
from .models import StoredAudio


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
            file_id: str,
            sample_rate: int = 48_000

    ) -> StoredAudio:
        if not file_id:
            file_id = f"{str(uuid4())}"
        key = (
            f"audio/"
            f"{speaker}/"
            f"{file_id}-{speaker}.wav"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_path = (
                    Path(temp_dir)
                    / "audio.wav"
            )

            self.tts.synthesize_to_file(
                text=text,
                output_path=temporary_path,
                sample_rate=sample_rate,
            )

            stored = self.storage.save(
                source=temporary_path,
                key=key,
                content_type="audio/wav",
            )

        return StoredAudio(
            key=stored.key,
            file_id=file_id,
            content_type=stored.content_type,
        )
