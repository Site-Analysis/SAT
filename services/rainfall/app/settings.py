from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RainfallSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = Field("*", validation_alias="CORS_ORIGINS")
    # TODO: Replace synthetic rainfall generator with Open-Meteo integration
    default_source: str = Field("synthetic", validation_alias="RAINFALL_DEFAULT_SOURCE")
