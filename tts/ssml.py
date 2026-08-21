from __future__ import annotations

import html
import re

from .models import Pause, Sentence

TOKEN_RE = re.compile(
    r"\w+(?:\+\w+)*|[^\w\s]",
    re.UNICODE,
)


class SSMLRenderer:
    """
    Собирает SSML из:
    - исходного предложения;
    - текста после accentizer;
    - списка Pause.
    """

    def render(
            self,
            sentence: Sentence,
            stressed_text: str | None,
            pauses: list[Pause],
    ) -> str:

        original_tokens = [
            token.text
            for token in sentence.tokens
        ]
        aligned = original_tokens
        if stressed_text:
            stressed_tokens = self._tokenize(
                stressed_text
            )
            aligned = self._align_tokens(
                original_tokens,
                stressed_tokens,
            )

        if aligned is None:
            # Безопасный fallback:
            # если alignment не удался,
            # лучше вернуть stressed_text без SSML,
            # чем испортить ударения.
            if stressed_text:
                return self._escape_text(
                    stressed_text
                )

        pause_map = {
            pause.before_token: pause
            for pause in pauses
        }

        parts: list[str] = []

        for index, token in enumerate(
                aligned
        ):

            pause = pause_map.get(index)

            if pause is not None:
                parts.append(
                    self._break(
                        pause.duration_ms
                    )
                )

            parts.append(
                self._escape_text(token)
            )

            # Пробел между токенами.
            if index + 1 < len(aligned):
                if self._needs_space(
                        token,
                        aligned[index + 1],
                ):
                    parts.append(" ")

        return "".join(parts)

    # ---------------------------------------------------------
    # Tokenization
    # ---------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return TOKEN_RE.findall(text)

    # ---------------------------------------------------------
    # Alignment
    # ---------------------------------------------------------

    def _align_tokens(
            self,
            original: list[str],
            stressed: list[str],
    ) -> list[str] | None:

        if len(original) != len(stressed):
            return self._align_fuzzy(
                original,
                stressed,
            )

        for left, right in zip(
                original,
                stressed,
        ):
            if not self._same_token(left, right):
                return self._align_fuzzy(
                    original,
                    stressed,
                )

        return stressed

    def _align_fuzzy(
            self,
            original: list[str],
            stressed: list[str],
    ) -> list[str] | None:

        result: list[str] = []

        stressed_index = 0

        for original_token in original:

            found = False

            while stressed_index < len(
                    stressed
            ):
                candidate = stressed[
                    stressed_index
                ]

                stressed_index += 1

                if self._same_token(
                        original_token,
                        candidate,
                ):
                    result.append(candidate)
                    found = True
                    break

            if not found:
                return None

        # Важная проверка:
        # нельзя молча потерять хвост текста.
        if stressed_index != len(stressed):
            return None

        return result

    @staticmethod
    def _same_token(
            left: str,
            right: str,
    ) -> bool:

        left = SSMLRenderer._normalize_token(
            left
        )

        right = SSMLRenderer._normalize_token(
            right
        )

        return left == right

    @staticmethod
    def _normalize_token(
            token: str,
    ) -> str:

        # Ударение ruaccent.
        token = token.replace("+", "")

        # Кавычки/пунктуация.
        token = token.lower()

        return token

    # ---------------------------------------------------------
    # Formatting
    # ---------------------------------------------------------

    @staticmethod
    def _needs_space(
            current: str,
            following: str,
    ) -> bool:

        # Перед пунктуацией пробел не нужен.
        if following in {
            ".",
            ",",
            "!",
            "?",
            ";",
            ":",
            "%",
            "»",
            ")",
            "]",
            # "—",
            # "–",
            "\""
        }:
            return False

        # После открывающей пунктуации пробел не нужен.
        if current in {
            "«",
            "(",
            "[",
            "\""
        }:
            return False

        return True

    @staticmethod
    def _break(
            milliseconds: int,
    ) -> str:

        if milliseconds <= 0:
            return ""

        return (
            f'<break time="{milliseconds}ms"/>'
        )

    @staticmethod
    def _escape_text(text: str) -> str:
        return html.escape(
            text,
            quote=False,
        )
