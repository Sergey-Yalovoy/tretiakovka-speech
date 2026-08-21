# audio/tts/silero.py

import re
import wave
from pathlib import Path

import torch
from ru_normalizr import normalize, NormalizeOptions

from tts.pipeline import TTSPipeline


class SileroTTS:

    MODEL_URL = (
        "https://models.silero.ai/models/tts/ru/v5_ru.pt"
    )

    def __init__(
        self,
        model_path: str = "models/v5_5_ru.pt",
        speaker: str = "baya",
        max_chunk_size: int = 1000,
    ):
        self.model_path = Path(model_path)
        self.speaker = speaker
        self.max_chunk_size = max_chunk_size

        torch.set_num_threads(4)

        self._ensure_model()

        self.model = (
            torch.package.PackageImporter(
                str(self.model_path)
            )
            .load_pickle(
                "tts_models",
                "model",
            )
        )

        self.model.to(
            torch.device("cpu")
        )

        self.tts_pipeline = TTSPipeline(
            make_accentuate=True,
        )

    def _ensure_model(self) -> None:

        if self.model_path.exists():
            return

        self.model_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        torch.hub.download_url_to_file(
            self.MODEL_URL,
            str(self.model_path),
        )

    def _split_text(
        self,
        text: str,
    ) -> list[str]:

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        if len(text) <= self.max_chunk_size:
            return [text]

        sentences = re.split(
            r"(?<=[.!?…])\s+",
            text,
        )

        chunks: list[str] = []
        current = ""

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            if len(sentence) <= self.max_chunk_size:

                if not current:
                    current = sentence

                elif (
                    len(current)
                    + 1
                    + len(sentence)
                    <= self.max_chunk_size
                ):
                    current += " " + sentence

                else:
                    chunks.append(current)
                    current = sentence

                continue

            if current:
                chunks.append(current)
                current = ""

            chunks.extend(
                self._split_long_sentence(
                    sentence
                )
            )

        if current:
            chunks.append(current)

        return chunks

    def _split_long_sentence(
        self,
        sentence: str,
    ) -> list[str]:

        words = sentence.split()

        chunks: list[str] = []
        current = ""

        for word in words:

            if not current:
                current = word
                continue

            candidate = (
                f"{current} {word}"
            )

            if len(candidate) <= self.max_chunk_size:
                current = candidate

            else:
                chunks.append(current)
                current = word

        if current:
            chunks.append(current)

        return chunks

    def _normalize_text(
        self,
        text: str,
    ) -> str:

        options = NormalizeOptions.tts(
            initials_vowel_mode="double",
            initials_pause_mode="comma",
        )

        return normalize(
            text,
            options,
        )

    def _generate_chunk_from_ssml(
        self,
        text: str,
        output_path: Path,
        sample_rate: int,
    ) -> None:

        self.model.save_wav(
            ssml_text=text,
            speaker=self.speaker,
            sample_rate=sample_rate,
            audio_path=str(output_path),
        )

    def _merge_wav_files(
        self,
        input_paths: list[Path],
        output_path: Path,
    ) -> None:

        if not input_paths:
            raise ValueError(
                "No audio chunks to merge"
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with wave.open(
            str(input_paths[0]),
            "rb",
        ) as first:

            params = first.getparams()

            with wave.open(
                str(output_path),
                "wb",
            ) as output:

                output.setparams(params)

                output.writeframes(
                    first.readframes(
                        first.getnframes()
                    )
                )

                for path in input_paths[1:]:

                    with wave.open(
                        str(path),
                        "rb",
                    ) as chunk:

                        output.writeframes(
                            chunk.readframes(
                                chunk.getnframes()
                            )
                        )

    def synthesize_to_file(
        self,
        text: str,
        output_path: str | Path,
        sample_rate: int = 48_000,
    ) -> Path:

        text = text.strip()

        if not text:
            raise ValueError(
                "Text cannot be empty"
            )

        output_path = Path(output_path)

        # 1. Normalize

        text = self._normalize_text(text)

        # 2. Split

        chunks = self._split_text(text)

        # 3. SSML

        ssml_chunks: list[str] = []

        for chunk in chunks:

            ssml = self.tts_pipeline.process(
                chunk
            )

            ssml_chunks.append(ssml)

        # 4. Single chunk

        if len(ssml_chunks) == 1:

            self._generate_chunk_from_ssml(
                text=ssml_chunks[0],
                output_path=output_path,
                sample_rate=sample_rate,
            )

            return output_path

        # 5. Multiple chunks

        chunks_dir = (
            output_path.parent
            / f".{output_path.stem}_chunks"
        )

        chunks_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        chunk_paths: list[Path] = []

        try:

            for index, ssml in enumerate(
                ssml_chunks
            ):

                chunk_path = (
                    chunks_dir
                    / f"chunk_{index:04d}.wav"
                )

                self._generate_chunk_from_ssml(
                    text=ssml,
                    output_path=chunk_path,
                    sample_rate=sample_rate,
                )

                chunk_paths.append(
                    chunk_path
                )

            self._merge_wav_files(
                input_paths=chunk_paths,
                output_path=output_path,
            )

        finally:

            for chunk_path in chunk_paths:
                chunk_path.unlink(
                    missing_ok=True
                )

            try:
                chunks_dir.rmdir()
            except OSError:
                pass

        return output_path