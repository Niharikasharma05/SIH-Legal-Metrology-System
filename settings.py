"""Single, typed source of runtime configuration for the local stack."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str
    jwt_secret: str = "change-this-development-secret-before-production"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "setucheck"

    @property
    def is_local(self) -> bool:
        return self.app_env in {"development", "test", "local"}

    @property
    def async_database_url(self) -> str:
        """Use asyncpg only for the FastAPI Users authentication boundary."""
        return self.database_url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
