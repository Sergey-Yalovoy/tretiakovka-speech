from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Token:
    """
    Токен Natasha.

    text:
        Текст без ударений.

    stressed:
        Текст после ruaccent.
    """

    text: str
    index: int

    syntax_id: str | None = None
    head_id: str | None = None
    relation: str | None = None

    stressed: str | None = None


@dataclass
class Sentence:
    text: str
    tokens: list[Token] = field(default_factory=list)


@dataclass(frozen=True)
class Pause:
    """
    Пауза перед токеном.

    before_token:
        Индекс токена, перед которым ставим break.
    """

    before_token: int
    duration_ms: int
    reason: str


@dataclass
class ProsodyResult:
    sentence: Sentence
    pauses: list[Pause] = field(default_factory=list)
