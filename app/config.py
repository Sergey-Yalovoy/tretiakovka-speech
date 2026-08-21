from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
print(BASE_DIR)


class Settings(BaseSettings):
    # Приложение
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    # База данных
    db_user: str = Field(..., alias="DB_USER")
    db_password: SecretStr = Field(..., alias="DB_PASSWORD")
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(..., alias="DB_NAME")
    db_echo: bool = Field(default=False, alias="DB_ECHO")
    tretyakov_lang: str = "ru"
    http_timeout: float = 20.0
    tretyakov_base_url: str = (
        "https://my.tretyakov.ru/api/v1"
    )
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
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
