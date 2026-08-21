from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StorageObject:
    key: str
    content_type: str
    size: int


@dataclass(frozen=True)
class StorageRange:
    start: int
    end: int
    size: int

    @property
    def length(self) -> int:
        return self.end - self.start + 1


class FileStorage(ABC):

    @abstractmethod
    def save(
        self,
        source: Path,
        key: str,
        content_type: str,
    ) -> StorageObject:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        key: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def stat(
        self,
        key: str,
    ) -> StorageObject:
        raise NotImplementedError

    @abstractmethod
    def get_url(
        self,
        key: str,
        expires: int = 3600,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def stream(
        self,
        key: str,
        start: int = 0,
        end: int | None = None,
        chunk_size: int = 1024 * 1024,
    ) -> Iterator[bytes]:
        raise NotImplementedError