from pathlib import Path
import sys


def get_application_root() -> Path:
    """Return a stable root independent of the process working directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def get_resource_path(relative: str) -> Path:
    bundle = getattr(sys, "_MEIPASS", None)
    return (Path(bundle) if bundle else get_application_root()) / relative


def resource_path(relative: str) -> Path:
    """Backward-compatible alias."""
    return get_resource_path(relative)
