from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gee_project_id: str = Field(validation_alias="GEE_PROJECT_ID")
    gee_service_account_email: str = Field(validation_alias="GEE_SERVICE_ACCOUNT_EMAIL")
    gee_service_account_key_path: Path = Field(
        validation_alias=AliasChoices(
            "GEE_SERVICE_ACCOUNT_KEY_PATH",
            "GEE_SA_KEY_PATH",
        )
    )
