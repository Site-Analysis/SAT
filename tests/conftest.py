"""Pytest configuration for SAT integration tests."""
import sys
from pathlib import Path

# Add each service's directory to sys.path so tests can import app/
SERVICES_ROOT = Path(__file__).resolve().parents[1] / "services"
for service_dir in SERVICES_ROOT.iterdir():
    if service_dir.is_dir() and (service_dir / "app").exists():
        sys.path.insert(0, str(service_dir))
