"""Centralised, type-checked settings loaded from environment / .env."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str = "taxi"
    postgres_password: str = "taxi"
    postgres_db: str = "taxi"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    api_title: str = "Urban Mobility Data Explorer"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:8080,http://localhost:8081"  # comma-separated list of allowed CORS origins for the API

    # pipeline default batch size
    trip_batch_size: int = 50_000

    @property
    def async_db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_db_url(self) -> str:
        # will be used by Alembic and the geopandas-based ETL (psycopg2).
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
