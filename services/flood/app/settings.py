from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FloodSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = Field("*", validation_alias="CORS_ORIGINS")
    data_source: str = Field("deterministic-fallback", validation_alias="FLOOD_DATA_SOURCE")

    gee_project_id: str | None = Field(None, validation_alias="GEE_PROJECT_ID")
    gee_service_account_email: str | None = Field(None, validation_alias="GEE_SERVICE_ACCOUNT_EMAIL")
    gee_service_account_key_path: str | None = Field(
        None,
        validation_alias=AliasChoices("GEE_SERVICE_ACCOUNT_KEY_PATH", "GEE_SA_KEY_PATH"),
    )
