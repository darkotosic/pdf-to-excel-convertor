from pathlib import Path


def default_output_path(source: Path) -> Path:
    return source.with_suffix(".xlsx")
