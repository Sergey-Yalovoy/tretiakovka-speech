import shutil
from collections.abc import Iterator
from pathlib import Path

from .base import FileStorage, StorageObject


class LocalFileStorage(FileStorage):

    def __init__(
            self,
            root: str | Path,
            base_url: str = "/media/",
    ):
        self.root = Path(root).expanduser().resolve()
        self.base_url = base_url.rstrip("/") + "/"

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _resolve(
            self,
            key: str,
    ) -> Path:
        path = (self.root / key).resolve()

        # Защита от ../
        if self.root not in path.parents:
            raise ValueError(
                f"Invalid storage key: {key}"
            )

        return path

    def save(
            self,
            source: Path,
            key: str,
            content_type: str,
    ) -> StorageObject:

        destination = self._resolve(key)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            destination,
        )

        return StorageObject(
            key=key,
            content_type=content_type,
            size=destination.stat().st_size,
        )

    def delete(
            self,
            key: str,
    ) -> None:

        path = self._resolve(key)

        path.unlink(
            missing_ok=True,
        )

    def stat(
            self,
            key: str,
    ) -> StorageObject:

        path = self._resolve(key)

        if not path.is_file():
            raise FileNotFoundError(key)

        return StorageObject(
            key=key,
            content_type=self._detect_content_type(
                path
            ),
            size=path.stat().st_size,
        )

    def get_url(
            self,
            key: str,
            expires: int = 3600,
    ) -> str:

        return (
            f"{self.base_url}"
            f"{key}"
        )

    def stream(
            self,
            key: str,
            start: int = 0,
            end: int | None = None,
            chunk_size: int = 1024 * 1024,
    ) -> Iterator[bytes]:

        path = self._resolve(key)

        if not path.is_file():
            raise FileNotFoundError(key)

        file_size = path.stat().st_size

        if start < 0:
            raise ValueError(
                "start cannot be negative"
            )

        if start >= file_size:
            return

        if end is None:
            end = file_size - 1

        end = min(
            end,
            file_size - 1,
        )

        if end < start:
            raise ValueError(
                "end cannot be less than start"
            )

        remaining = end - start + 1

        with path.open("rb") as file:

            file.seek(start)

            while remaining > 0:

                chunk = file.read(
                    min(
                        chunk_size,
                        remaining,
                    )
                )

                if not chunk:
                    break

                remaining -= len(chunk)

                yield chunk

    @staticmethod
    def _detect_content_type(
            path: Path,
    ) -> str:

        suffix = path.suffix.lower()

        content_types = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".ogg": "audio/ogg",
            ".opus": "audio/ogg",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
        }

        return content_types.get(
            suffix,
            "application/octet-stream",
        )

# example

# storage = LocalAudioStorage(
#     root="/app/media",
# )
#
# key = storage.save(
#     source=Path("/tmp/audio.wav"),
#     key="audio/123.wav",
# )

# print(key)
# audio/123.wav

# print(storage.url(key))
# /media/audio/123.wav
