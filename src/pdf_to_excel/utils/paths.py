from pathlib import Path


def resource_path(relative: str) -> Path:
    return Path(__file__).resolve().parents[3] / relative
