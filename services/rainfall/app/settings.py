from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RainfallSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = Field("*", validation_alias="CORS_ORIGINS")
    default_source: str = Field("open-meteo", validation_alias="RAINFALL_DEFAULT_SOURCE")
