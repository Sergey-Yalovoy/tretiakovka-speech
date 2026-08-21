from __future__ import annotations

from dataclasses import dataclass

from .accent import RuAccentizer
from .models import Pause, Sentence
from .prosody import ProsodyAnalyzer
from .ssml import SSMLRenderer
from .syntax import SyntaxAnalyzer


@dataclass
class ProcessedSentence:
    sentence: Sentence
    stressed_text: str
    pauses: list[Pause]


class TTSPipeline:

    def __init__(self, make_accentuate=False) -> None:
        self.syntax = SyntaxAnalyzer()
        self.prosody = ProsodyAnalyzer()
        self.accent = RuAccentizer()
        self.renderer = SSMLRenderer()
        self.make_accentuate = make_accentuate

    def process(
        self,
        text: str,
    ) -> str:

        sentences = self.syntax.analyze(
            text
        )

        rendered_sentences: list[str] = []

        for sentence in sentences:

            # Natasha analysis.
            prosody = self.prosody.analyze(
                sentence
            )
            stressed_text = None
            if self.make_accentuate:
                # Accentizer получает ПОЛНОЕ предложение.
                stressed_text = self.accent.accentuate(
                    sentence.text
                )

            # SSML.
            rendered = self.renderer.render(
                sentence=sentence,
                stressed_text=stressed_text,
                pauses=prosody.pauses,
            )

            rendered_sentences.append(
                f"<s>{rendered}</s>"
            )

        return (
            "<speak>"
            "<p>"
            + "\n".join(rendered_sentences)
            + "</p>"
            "</speak>"
        )