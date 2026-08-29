from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from .document import ConversionStatus, ConversionWarning
from .table import ExtractedTable


class OCRMode(StrEnum):
    AUTOMATIC = "automatic"
    ALWAYS = "always"
    NEVER = "never"


class OutputMode(StrEnum):
    STRUCTURED = "structured"
    PRESERVE_TABLES = "preserve_tables"
    BOTH = "both"


@dataclass(frozen=True, slots=True)
class ConversionOptions:
    input_path: Path
    output_path: Path
    pages: tuple[int, ...] | None = None
    ocr_mode: OCRMode = OCRMode.AUTOMATIC
    languages: tuple[str, ...] = ("srp", "srp_latn", "eng")
    dpi: int = 300
    output_mode: OutputMode = OutputMode.BOTH
    include_empty_template_rows: bool = False


@dataclass(slots=True)
class ConversionResult:
    output_path: Path
    status: ConversionStatus = ConversionStatus.SUCCESS
    tables: list[ExtractedTable] = field(default_factory=list)
    pages_processed: int = 0
    structured_documents: list[object] = field(default_factory=list)
    warnings: list[ConversionWarning] = field(default_factory=list)
    total_pages: int = 0
    native_pages: int = 0
    ocr_pages: int = 0
    mixed_pages: int = 0
    tables_detected: int = 0
    records_exported: int = 0
    duration_seconds: float = 0.0
