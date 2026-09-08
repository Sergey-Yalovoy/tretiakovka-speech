import io
import re
from pathlib import Path

import av
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
            target_bitrate: int = 64_000,  # Bitrate для Opus (64 kbps идеален для речи)
    ):
        self.model_path = Path(model_path)
        self.speaker = speaker
        self.max_chunk_size = max_chunk_size
        self.target_bitrate = target_bitrate

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

        partial_path = (
            self.model_path
            .with_suffix(".pt.part")
        )

        torch.hub.download_url_to_file(
            self.MODEL_URL,
            str(partial_path),
        )

        import os
        os.replace(
            partial_path,
            self.model_path,
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

    def _generate_audio_tensor(
            self,
            ssml_text: str,
            sample_rate: int,
    ) -> torch.Tensor:
        """
        Генерирует аудио с помощью Silero напрямую в RAM как torch.Tensor.
        """
        # apply_tts генерирует 1D тензор float32 аудио-сэмплов
        audio_tensor = self.model.apply_tts(
            ssml_text=ssml_text,
            speaker=self.speaker,
            sample_rate=sample_rate,
        )
        return audio_tensor

    def _save_tensor_as_opus(
            self,
            audio_tensor: torch.Tensor,
            output_path: Path,
            sample_rate: int,
    ) -> None:
        """
        Преобразует torch.Tensor (float32) и кодирует в Opus (OGG) через PyAV.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Конвертируем PyTorch тензор в NumPy массив (1, N) для стерео/моно формата
        audio_np = audio_tensor.unsqueeze(0).cpu().numpy()

        # Создаем контейнер для записи OGG/Opus
        container = av.open(str(output_path), mode="w", format="ogg")
        stream = container.add_stream("libopus", rate=sample_rate)
        stream.bit_rate = self.target_bitrate
        stream.options = {"application": "audio"}

        # Преобразуем numpy-массив во фрейм PyAV
        frame = av.AudioFrame.from_ndarray(
            audio_np,
            format="flt",  # float32 (-1.0 to 1.0)
            layout="mono"
        )
        frame.sample_rate = sample_rate

        # Кодируем и сохраняем
        for packet in stream.encode(frame):
            container.mux(packet)

        for packet in stream.encode():
            container.mux(packet)

        container.close()

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
        ssml_chunks = [self.tts_pipeline.process(chunk) for chunk in chunks]

        # 4. Генерация тензоров аудио напрямую в RAM
        audio_tensors: list[torch.Tensor] = []
        for ssml in ssml_chunks:
            tensor = self._generate_audio_tensor(
                ssml_text=ssml,
                sample_rate=sample_rate,
            )
            audio_tensors.append(tensor)

        # 5. Объединение тензоров в один (если чанков несколько)
        if len(audio_tensors) == 1:
            full_audio = audio_tensors[0]
        else:
            full_audio = torch.cat(audio_tensors, dim=0)

        # 6. Кодирование в Opus и сохранение по назначению
        self._save_tensor_as_opus(
            audio_tensor=full_audio,
            output_path=output_path,
            sample_rate=sample_rate,
        )

        return output_path
