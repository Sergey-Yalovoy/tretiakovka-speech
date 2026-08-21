from __future__ import annotations

from stressonnx import StressPipeline


class RuAccentizer:
    """
    Обёртка над stressonnx + ruaccent.

    Accentizer получает целое предложение,
    поэтому ruaccent имеет контекст.
    """

    def __init__(self) -> None:
        self.pipeline = StressPipeline()

    def accentuate(
        self,
        text: str,
    ) -> str:

        return self.pipeline.stress(
            text,
            "ru",
            model="ruaccent",
            fallback=False,
            notation="plus",

        )