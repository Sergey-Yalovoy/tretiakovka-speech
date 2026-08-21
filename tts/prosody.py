from __future__ import annotations

from .models import Pause, ProsodyResult, Sentence


class ProsodyAnalyzer:
    """
    Осторожный анализ просодии для Silero TTS.

    Основной источник интонации:
        пунктуация.

    Natasha используется только для определения
    крупных синтаксических конструкций.

    ВАЖНО:
    не ставим паузы на obl/nmod/amod и т.п.
    """

    # Явные паузы.
    SEMICOLON_PAUSE = 280
    COLON_PAUSE = 220
    DASH_PAUSE = 220

    # Синтаксические конструкции.
    CLAUSE_PAUSE = 180
    PARATAXIS_PAUSE = 220

    # Только действительно безопасные отношения.
    CLAUSE_RELATIONS = {
        "acl:relcl",
        "advcl",
        "ccomp",
    }

    def analyze(
        self,
        sentence: Sentence,
    ) -> ProsodyResult:

        pauses: list[Pause] = []

        self._punctuation_pauses(
            sentence,
            pauses,
        )

        self._syntactic_pauses(
            sentence,
            pauses,
        )

        return ProsodyResult(
            sentence=sentence,
            pauses=self._deduplicate(pauses),
        )

    # =========================================================
    # Punctuation
    # =========================================================

    def _punctuation_pauses(
        self,
        sentence: Sentence,
        pauses: list[Pause],
    ) -> None:

        tokens = sentence.tokens

        for index, token in enumerate(tokens):

            # -------------------------------------------------
            # ;
            # -------------------------------------------------

            if token.text == ";":

                if index + 1 < len(tokens):

                    pauses.append(
                        Pause(
                            before_token=index + 1,
                            duration_ms=self.SEMICOLON_PAUSE,
                            reason="semicolon",
                        )
                    )

            # -------------------------------------------------
            # :
            # -------------------------------------------------

            elif token.text == ":":

                if index + 1 < len(tokens):

                    pauses.append(
                        Pause(
                            before_token=index + 1,
                            duration_ms=self.COLON_PAUSE,
                            reason="colon",
                        )
                    )

            # -------------------------------------------------
            # —
            #
            # ВАЖНО:
            #
            # Не ставим break после тире.
            #
            # Вместо:
            #
            #     слово — <break/> продолжение
            #
            # оставляем:
            #
            #     слово — продолжение
            #
            # Само тире уже участвует в просодии.
            # -------------------------------------------------

    # =========================================================
    # Syntax
    # =========================================================

    def _syntactic_pauses(
        self,
        sentence: Sentence,
        pauses: list[Pause],
    ) -> None:

        tokens = sentence.tokens

        for index, token in enumerate(tokens):

            relation = token.relation

            if relation in self.CLAUSE_RELATIONS:

                self._relative_clause(
                    sentence,
                    index,
                    pauses,
                )

            # elif relation == "parataxis":
            #
            #     self._parataxis(
            #         sentence,
            #         index,
            #         pauses,
            #     )

    # =========================================================
    # Relative / subordinate clause
    # =========================================================

    def _relative_clause(
        self,
        sentence: Sentence,
        root_index: int,
        pauses: list[Pause],
    ) -> None:

        subtree = self._subtree(
            sentence,
            root_index,
        )

        if not subtree:
            return

        start = min(subtree)
        end = max(subtree)

        tokens = sentence.tokens

        # -----------------------------------------------------
        # Проверяем начало конструкции.
        #
        # Если непосредственно перед ней запятая,
        # значит синтаксический блок действительно
        # выделен пунктуацией.
        # -----------------------------------------------------

        if start > 0:

            previous = tokens[start - 1]

            if previous.text == ",":

                pauses.append(
                    Pause(
                        before_token=start,
                        duration_ms=self.CLAUSE_PAUSE,
                        reason="clause_start",
                    )
                )

        # -----------------------------------------------------
        # Проверяем конец конструкции.
        # -----------------------------------------------------

        if end + 1 < len(tokens):

            following = tokens[end + 1]

            if following.text == ",":

                pauses.append(
                    Pause(
                        before_token=end + 2,
                        duration_ms=self.CLAUSE_PAUSE,
                        reason="clause_end",
                    )
                )

    # =========================================================
    # Parataxis
    # =========================================================

    def _parataxis(
        self,
        sentence: Sentence,
        index: int,
        pauses: list[Pause],
    ) -> None:

        tokens = sentence.tokens

        # Если parataxis начинается после тире,
        # НЕ добавляем дополнительный break.
        #
        # Например:
        #
        # памятник — белый куб
        #
        # не:
        #
        # памятник — <break/> белый куб

        if index > 0:

            previous = tokens[index - 1]

            if previous.text in {
                "—",
                "–",
            }:
                return

        # Аналогично не ставим паузу,
        # если уже есть явная пунктуация.
        if index > 0:

            previous = tokens[index - 1]

            if previous.text in {
                ",",
                ";",
                ":",
            }:
                return

        pauses.append(
            Pause(
                before_token=index,
                duration_ms=self.PARATAXIS_PAUSE,
                reason="parataxis",
            )
        )

    # =========================================================
    # Dependency tree
    # =========================================================

    def _subtree(
        self,
        sentence: Sentence,
        root_index: int,
    ) -> list[int]:

        tokens = sentence.tokens

        id_to_index = {
            token.syntax_id: index
            for index, token in enumerate(tokens)
            if token.syntax_id is not None
        }

        children: dict[int, list[int]] = {}

        for index, token in enumerate(tokens):

            if token.head_id is None:
                continue

            head_index = id_to_index.get(
                token.head_id
            )

            if head_index is None:
                continue

            children.setdefault(
                head_index,
                [],
            ).append(index)

        result: list[int] = []

        stack = [root_index]

        while stack:

            current = stack.pop()

            if current in result:
                continue

            result.append(current)

            stack.extend(
                children.get(
                    current,
                    [],
                )
            )

        return result

    # =========================================================
    # Helpers
    # =========================================================

    @staticmethod
    def _deduplicate(
        pauses: list[Pause],
    ) -> list[Pause]:

        result: dict[int, Pause] = {}

        for pause in pauses:

            existing = result.get(
                pause.before_token
            )

            if existing is None:
                result[pause.before_token] = pause

            elif (
                pause.duration_ms
                > existing.duration_ms
            ):
                result[pause.before_token] = pause

        return sorted(
            result.values(),
            key=lambda item: item.before_token,
        )