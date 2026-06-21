# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RainfallSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = Field("*", validation_alias="CORS_ORIGINS")
    default_source: str = Field(
        "CHIRPS Daily via Google Earth Engine", validation_alias="RAINFALL_DEFAULT_SOURCE"
    )

    gee_project_id: str | None = Field(None, validation_alias="GEE_PROJECT_ID")
    gee_service_account_email: str | None = Field(
        None, validation_alias="GEE_SERVICE_ACCOUNT_EMAIL"
    )
    gee_service_account_key_path: str | None = Field(
        None,
        validation_alias=AliasChoices("GEE_SERVICE_ACCOUNT_KEY_PATH", "GEE_SA_KEY_PATH"),
    )
