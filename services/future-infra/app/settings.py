# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FutureInfraSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    cors_origins: str = Field("*", validation_alias="CORS_ORIGINS")
