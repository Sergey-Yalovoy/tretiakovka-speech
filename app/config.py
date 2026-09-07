from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Приложение
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # База данных
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: SecretStr = Field(default="postgres", alias="DB_PASSWORD")
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="tretyakov", alias="DB_NAME")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    # Tretyakov API
    tretyakov_lang: str = "ru"
    http_timeout: float = 20.0
    tretyakov_base_url: str = (
        "https://my.tretyakov.ru/api/v1"
    )

    # Хранилище файлов: "s3" | "local"
    storage_backend: str = Field(default="s3", alias="STORAGE_BACKEND")

    # S3 / MinIO
    s3_endpoint_url: str = Field(
        default="http://localhost:9000",
        alias="S3_ENDPOINT_URL",
    )
    s3_bucket: str = Field(default="audio", alias="S3_BUCKET")
    s3_access_key: str = Field(default="minioadmin", alias="S3_ACCESS_KEY")
    s3_secret_key: SecretStr = Field(
        default="minioadmin",
        alias="S3_SECRET_KEY",
    )
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_public_url: str | None = Field(default=None, alias="S3_PUBLIC_URL")

    # Локальное хранилище (STORAGE_BACKEND=local)
    media_root: Path = Field(
        default=BASE_DIR / "media",
        alias="MEDIA_ROOT",
    )

    # TTS
    tts_model_path: str = Field(
        default="models/v5_5_ru.pt",
        alias="TTS_MODEL_PATH",
    )
    tts_speaker: str = Field(default="baya", alias="TTS_SPEAKER")
    audio_sample_rate: int = Field(default=48_000, alias="AUDIO_SAMPLE_RATE")

    # Автоматический парсер
    sync_on_startup: bool = Field(default=True, alias="SYNC_ON_STARTUP")
    sync_interval_seconds: int = Field(
        default=24 * 60 * 60,
        alias="SYNC_INTERVAL_SECONDS",
    )
    sync_page_size: int = Field(default=1000, alias="SYNC_PAGE_SIZE")
    sync_max_pages: int | None = Field(default=None, alias="SYNC_MAX_PAGES")
    sync_detail_concurrency: int = Field(default=4, alias="SYNC_DETAIL_CONCURRENCY")
    sync_request_delay: float = Field(default=0.1, alias="SYNC_REQUEST_DELAY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: SecretStr | None = Field(
        default=None,
        alias="REDIS_PASSWORD",
    )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            password = self.redis_password.get_secret_value()
            return (
                f"redis://:{password}@"
                f"{self.redis_host}:{self.redis_port}/"
                f"{self.redis_db}"
            )

        return (
            f"redis://"
            f"{self.redis_host}:{self.redis_port}/"
            f"{self.redis_db}"
        )

    @property
    def db_url(self) -> str:
        password = self.db_password.get_secret_value()

        return (
            f"postgresql+asyncpg://"
            f"{self.db_user}:{password}@"
            f"{self.db_host}:{self.db_port}/"
            f"{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
