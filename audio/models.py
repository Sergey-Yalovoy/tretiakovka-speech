from dataclasses import dataclass


@dataclass(frozen=True)
class StoredAudio:
    key: str
    content_type: str