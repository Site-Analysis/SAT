from dataclasses import dataclass
from pathlib import Path

from .settings import BackendSettings


@dataclass(frozen=True)
class GeeCredentialsConfig:
    project_id: str
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
