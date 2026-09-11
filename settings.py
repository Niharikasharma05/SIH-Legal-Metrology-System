"""Single, typed source of runtime configuration for the local stack."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "setucheck"

    @property
    def is_local(self) -> bool:
        return self.app_env in {"development", "test", "local"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
