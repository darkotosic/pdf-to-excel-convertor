from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from .table import ExtractedTable


class OCRMode(StrEnum):
    AUTOMATIC = "automatic"
    ALWAYS = "always"
    NEVER = "never"


@dataclass(frozen=True, slots=True)
class ConversionOptions:
    input_path: Path
    output_path: Path
    pages: tuple[int, ...] | None = None
    ocr_mode: OCRMode = OCRMode.AUTOMATIC
    languages: tuple[str, ...] = ("srp", "srp_latn", "eng")
    dpi: int = 300


@dataclass(slots=True)
class ConversionResult:
    output_path: Path
    tables: list[ExtractedTable] = field(default_factory=list)
    pages_processed: int = 0
