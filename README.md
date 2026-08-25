# Tretyakov Speech

> ⚠️ **Проект находится на этапе активной разработки.** API и структура кода могут существенно меняться. Стабильность не гарантируется.

Генератор аудиогидов для Третьяковской галереи: сервис получает данные о картинах из открытого API `my.tretyakov.ru`, синтезирует по их описанию озвучку (TTS) и хранит/стримит аудиофайлы.

## Возможности

- **Парсер данных Третьяковской галереи** — клиент официального API (`my.tretyakov.ru/api/v1`) с получением карточки картины: название, авторы, размеры, материалы, техники, описание, факты, изображения.
- **Синтез речи (TTS)** — озвучка текста через **Silero TTS v5** с полноценным пайплайном подготовки текста.
- **Хранилище аудио** — абстракция `FileStorage` с реализациями для локальной файловой системы и S3-совместимых хранилищ (MinIO, AWS S3, Yandex Object Storage).
- **Стриминг аудио** — отдача аудиофайлов чанками с поддержкой Range-запросов (`start` / `end`).
- **REST API** — FastAPI-эндпоинты для получения и парсинга картин.

## Архитектура

```
app/
├── api/            # HTTP-слой (FastAPI роутеры)
├── services/       # Бизнес-логика (ArtworkService)
├── repositories/   # Доступ к данным (SQLAlchemy)
├── db/             # Модели и сессии БД (PostgreSQL, async)
├── schemas/        # Pydantic-схемы запросов/ответов
├── tretyakov/      # Клиент API Третьяковской галереи
└── config.py       # Настройки (pydantic-settings)

tts/                # Пайплайн синтеза речи
├── silero_tts.py   # Обёртка над Silero TTS v5
├── pipeline.py     # Оркестрация обработки текста
├── syntax.py       # Синтаксический анализ (Natasha)
├── prosody.py      # Расстановка пауз
├── accent.py       # Расстановка ударений (stressonnx/ruaccent)
├── ssml.py         # Генерация SSML
└── models.py       # Доменные модели

audio/
├── service.py      # AudioService — генерация и сохранение аудио
└── models.py

storage/            # Абстракция хранилища файлов
├── base.py         # Интерфейс FileStorage
├── local.py        # Локальная ФС
└── s3.py           # S3-совместимое хранилище (boto3)
```

### Пайплайн TTS

Текст проходит несколько стадий перед синтезом:

1. **Нормализация** (`ru-normalizr`) — числа, даты, инициалы → читаемый текст.
2. **Разбиение на чанки** — длинный текст режется по предложениям (лимит ~1000 символов).
3. **Расстановка ударений** (`stressonnx` + ruaccent) — нотация `+`.
4. **Просодия** (`natasha`) — анализ синтаксиса и расстановка пауз `<break>`.
5. **SSML** — сборка разметки `<speak><p><s>...</s></p></speak>`.
6. **Silero TTS** — генерация WAV по чанкам и склейка в один файл.

## Технологии

| Категория | Технология |
|---|---|
| Язык | Python 3.12+ |
| API | FastAPI, uvicorn |
| БД | PostgreSQL (asyncpg), SQLAlchemy 2.0 async |
| Миграции | Alembic |
| Валидация | Pydantic v2, pydantic-settings |
| HTTP-клиент | httpx |
| TTS | Silero TTS v5, torch |
| NLP | natasha, ru-normalizr, stressonnx |
| Хранилище | boto3 (S3), локальная ФС |

## Установка

```bash
# Клонировать репозиторий
git clone <repo-url>
cd tretyakov-speech

# Создать виртуальное окружение и установить зависимости
poetry install

# Настроить переменные окружения
cp .env.example .env
# Отредактируйте .env: DB_USER, DB_PASSWORD, DB_NAME и т.д.
```

Модель Silero TTS скачивается автоматически при первом запуске (~500 МБ) в папку `models/`.

## Запуск

```bash
# Применить миграции
alembic upgrade head

# Запустить API
uvicorn app.main:app --reload
```

Swagger UI доступен по адресу: http://localhost:8000/docs

## Примеры использования

### 1. REST API — парсинг картины

```bash
curl -X POST "http://localhost:8000/api/v1/artworks/parse" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://my.tretyakov.ru/app/masterpiece/1234"}'
```

Ответ:

```json
{
  "id": 1234,
  "name": "Утро в сосновом лесу",
  "authors": [{"id": 1, "name": "Иван Шишкин", "years": "1832–1898"}],
  "height": "139",
  "width": "213",
  "facts": "...",
  "description": "...",
  "picture": ["..."],
  "picture_big": ["..."],
  "picture_thumb": ["..."]
}
```

Логика `get_or_fetch`: если картина уже есть в локальной БД — берётся из кеша, иначе запрашивается из API Третьяковки и сохраняется.

### 2. Получение картины из БД

```bash
curl "http://localhost:8000/api/v1/artworks/1234"
```

### 3. Клиент Третьяковской галереи напрямую

```python
import asyncio
import httpx

from app.tretyakov.client import TretyakovClient


async def main():
    async with httpx.AsyncClient(
        base_url="https://my.tretyakov.ru/api/v1",
        timeout=20,
    ) as http:
        client = TretyakovClient(http)

        detail = await client.gallery_by_id(1234)

        print(detail.name)
        print([a.name for a in detail.author])

        # Поиск по каталогу с фильтрами
        gallery = await client.gallery(
            page=1,
            page_size=18,
            authors=[42],
            styles=[7],
        )

        print(gallery.items)


asyncio.run(main())
```

### 4. Синтез речи (Silero TTS)

```python
from tts.silero_tts import SileroTTS

tts = SileroTTS(
    speaker="kseniya",     # aidar | baya | eugene | kseniya | xenia
    max_chunk_size=300,    # лимит длины чанка в символах
)

path = tts.synthesize_to_file(
    text="Утро в сосновом лесу — картина русских художников Ивана Шишкина и Константина Савицкого.",
    output_path="audio/guide_1234.wav",
    sample_rate=48_000,
)

print(path)  # audio/guide_1234.wav
```

Модель автоматически скачивается при первом использовании. Голоса: `aidar`, `baya`, `eugene`, `kseniya`, `xenia`.

### 5. Пайплайн обработки текста (без синтеза)

```python
from tts.pipeline import TTSPipeline

pipeline = TTSPipeline(make_accentuate=True)

ssml = pipeline.process("Здравствуйте! Добро пожаловать в Третьяковскую галерею.")

print(ssml)
# <speak><p><s>здравствуйте<break time="..."/> добро пожаловать ...</s></p></speak>
```

### 6. Генерация и сохранение аудио (AudioService)

```python
from audio.service import AudioService
from storage.local import LocalFileStorage
from tts.silero_tts import SileroTTS

storage = LocalFileStorage(root="./media")

tts = SileroTTS(speaker="kseniya")

audio_service = AudioService(tts=tts, storage=storage)

audio = audio_service.generate(text="Описание картины...")

print(audio.key)            # audio/<uuid>.wav
print(audio.content_type)   # audio/wav
print(storage.get_url(audio.key))  # /media/audio/<uuid>.wav
```

Для S3 достаточно подменить реализацию хранилища:

```python
from storage.s3 import S3FileStorage

storage = S3FileStorage(
    bucket="audio",
    endpoint_url="http://minio:9000",   # или None для AWS
    region_name="us-east-1",
    public_url="https://cdn.example.com",  # опционально: публичный URL вместо presigned
)
```

### 7. Стриминг аудио

```python
from storage.local import LocalFileStorage
from streaming import AudioStreamingService

storage = LocalFileStorage(root="./media")
streaming = AudioStreamingService(storage)

meta = streaming.get_metadata("audio/<uuid>.wav")
print(meta.size, meta.content_type)  # 8345678 audio/wav

# Потоковое чтение с позиции (для Range-запросов)
for chunk in streaming.stream("audio/<uuid>.wav", start=1024):
    ...
```

Оба хранилища (`LocalFileStorage` и `S3FileStorage`) поддерживают стриминг с диапазонами байт — это основа для будущей отдачи аудиогида с перемоткой.

## Переменные окружения

Основные настройки (см. `.env.example` и `app/config.py`):

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DB_USER` | Пользователь PostgreSQL | — |
| `DB_PASSWORD` | Пароль PostgreSQL | — |
| `DB_HOST` | Хост БД | `localhost` |
| `DB_PORT` | Порт БД | `5432` |
| `DB_NAME` | Имя базы данных | — |
| `DB_ECHO` | Логирование SQL-запросов | `false` |

## Roadmap

- [ ] **Полный парсер API** — обход всего каталога https://my.tretyakov.ru/app/gallery (авторы, стили, категории, периоды), массовая загрузка картин в БД.
- [ ] **Стриминг аудиогида** — эндпоинт отдачи готовой озвучки по конкретной картине, генерация QR-кодов со ссылкой на аудиогид.
- [ ] **React-приложение** — фронтенд для просмотра картин и прослушивания аудиогидов (сканирование QR-кода).

## Статус разработки

Проект в ранней стадии. Реализовано: парсинг отдельных картин, TTS-пайплайн, слой хранения и стриминга. Не реализовано: массовый парсинг каталога, привязка аудио к картинам, фронтенд.
