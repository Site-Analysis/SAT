# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ContourSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = Field("*", validation_alias="CORS_ORIGINS")
    service_port: int = Field(8010, validation_alias="SERVICE_PORT")
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")
    dem_source: str = Field("copernicus", validation_alias="CONTOUR_DEM_SOURCE")
    gee_project_id: str | None = Field(None, validation_alias="GEE_PROJECT_ID")
    gee_service_account_email: str | None = Field(
        None, validation_alias="GEE_SERVICE_ACCOUNT_EMAIL"
    )
    gee_service_account_key_path: str | None = Field(
        None,
        validation_alias=AliasChoices("GEE_SERVICE_ACCOUNT_KEY_PATH", "GEE_SA_KEY_PATH"),
    )
