from collections.abc import Iterator

from storage.base import StorageObject, FileStorage


class AudioStreamingService:

    def __init__(
            self,
            storage: FileStorage,
    ):
        self.storage = storage

    def get_metadata(
            self,
            key: str,
    ) -> StorageObject:
        return self.storage.stat(key)

    def stream(
            self,
            key: str,
            start: int = 0,
            end: int | None = None,
    ) -> Iterator[bytes]:
        return self.storage.stream(
            key=key,
            start=start,
            end=end,
        )
