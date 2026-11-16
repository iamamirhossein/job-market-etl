from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    app_name: str = Field("job-market-etl", min_length=1)
    app_version: str = "0.1.0"
    environment: Literal["local", "test", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["text", "json"] = "text"

    lake_endpoint_url: str = Field("http://localhost:9000", min_length=1)
    lake_access_key: str = Field("minioadmin", min_length=1)
    lake_secret_key: SecretStr = SecretStr("minioadmin")
    lake_bucket: str = Field(
        "job-market-lake",
        pattern=r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
