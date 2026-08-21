from __future__ import annotations

from natasha import (
    Doc,
    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    Segmenter,
)

from .models import Sentence, Token


class SyntaxAnalyzer:
    """
    Синтаксический анализ русского текста через Natasha.

    ВАЖНО:
    сюда передаётся текст без расставленных ударений.
    """

    def __init__(self) -> None:
        self.segmenter = Segmenter()

        self.embedding = NewsEmbedding()

        self.morph_tagger = NewsMorphTagger(
            self.embedding
        )

        self.syntax_parser = NewsSyntaxParser(
            self.embedding
        )

    def analyze(self, text: str) -> list[Sentence]:
        doc = Doc(text)

        doc.segment(self.segmenter)

        doc.tag_morph(self.morph_tagger)

        doc.parse_syntax(self.syntax_parser)

        sentences: list[Sentence] = []

        for doc_sentence in doc.sents:
            tokens: list[Token] = []

            for index, token in enumerate(
                doc_sentence.tokens
            ):
                tokens.append(
                    Token(
                        text=token.text,
                        index=index,
                        syntax_id=token.id,
                        head_id=token.head_id,
                        relation=token.rel,
                    )
                )

            sentences.append(
                Sentence(
                    text=doc_sentence.text,
                    tokens=tokens,
                )
            )

        return sentences