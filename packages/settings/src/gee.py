# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .settings import BackendSettings
except ImportError:  # Allows direct import when packages/settings/src is on sys.path.
    from settings import BackendSettings


@dataclass(frozen=True)
class GeeCredentialsConfig:
    project_id: str | None
    service_account_email: str
    service_account_key_path: Path


def load_gee_credentials_config(
    settings: BackendSettings | None = None,
) -> GeeCredentialsConfig:
    resolved = settings or BackendSettings()
    key_path = resolved.gee_service_account_key_path

    if not key_path.exists():
        raise FileNotFoundError(
            "GEE service account file not found at "
            f"{key_path}. Set GEE_SERVICE_ACCOUNT_KEY_PATH to a valid file."
        )

    return GeeCredentialsConfig(
        project_id=resolved.gee_project_id,
        service_account_email=resolved.gee_service_account_email,
        service_account_key_path=key_path,
    )


def initialize_gee(settings: BackendSettings | None = None) -> Any:
    """Initialize Earth Engine with the shared backend credentials."""
    import ee

    config = load_gee_credentials_config(settings)
    credentials = ee.ServiceAccountCredentials(
        config.service_account_email,
        str(config.service_account_key_path),
    )
    init_kwargs = {"project": config.project_id} if config.project_id else {}
    ee.Initialize(credentials, **init_kwargs)
    return ee
