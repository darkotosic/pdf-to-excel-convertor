from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from pathlib import Path

from .geometry import BoundingBox


class PageType(StrEnum):
    DIGITAL = "digital"
    SCANNED = "scanned"
    MIXED = "mixed"


class WordSource(StrEnum):
    NATIVE = "native"
    OCR = "ocr"


class ExtractionSource(StrEnum):
    """The source that actually supplied a page's extracted words."""

    NATIVE = "native"
    OCR = "ocr"
    HYBRID = "hybrid"


class WarningSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class WarningCode(StrEnum):
    RENDER_FALLBACK_USED = "RENDER_FALLBACK_USED"
    RENDER_FAILED = "RENDER_FAILED"
    PHANTOM_TEXT_SUPPRESSED = "PHANTOM_TEXT_SUPPRESSED"
    NATIVE_OCR_DISAGREEMENT = "NATIVE_OCR_DISAGREEMENT"
    OCR_LOW_CONFIDENCE = "OCR_LOW_CONFIDENCE"
    OCR_AMBIGUOUS_IDENTIFIER = "OCR_AMBIGUOUS_IDENTIFIER"
    INVALID_DATE = "INVALID_DATE"
    METADATA_UNCERTAIN = "METADATA_UNCERTAIN"
    FOOTER_UNCERTAIN = "FOOTER_UNCERTAIN"
    TABLE_LOW_CONFIDENCE = "TABLE_LOW_CONFIDENCE"
    PAGE_SKIPPED = "PAGE_SKIPPED"
    UNSPECIFIED = "UNSPECIFIED"


class ConversionStatus(StrEnum):
    SUCCESS = "success"
    SUCCESS_WITH_WARNINGS = "success_with_warnings"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class DocumentWord:
    text: str
    bbox: BoundingBox
    confidence: float
    page_number: int
    source: WordSource


@dataclass(frozen=True, slots=True)
class DetectedLine:
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    thickness: float = 1.0

    @property
    def horizontal(self) -> bool:
        return abs(self.end_y - self.start_y) <= abs(self.end_x - self.start_x)


@dataclass(frozen=True, slots=True)
class DetectedGrid:
    bbox: BoundingBox
    row_boundaries: tuple[float, ...]
    column_boundaries: tuple[float, ...]

    @property
    def row_count(self) -> int:
        return max(0, len(self.row_boundaries) - 1)

    @property
    def column_count(self) -> int:
        return max(0, len(self.column_boundaries) - 1)


@dataclass(slots=True)
class EquipmentItem:
    item_number: str = ""
    equipment_type: str = ""
    model: str = ""
    quantity: str = ""
    serial_number: str = ""
    inventory_number: str = ""
    confidence: float = 1.0

    @property
    def populated(self) -> bool:
        return any(
            value.strip()
            for value in (
                self.equipment_type,
                self.model,
                self.quantity,
                self.serial_number,
                self.inventory_number,
            )
        )


@dataclass(frozen=True, slots=True)
class ConversionWarning:
    message: str
    page_number: int
    row: int | None = None
    field: str | None = None
    value: str = ""
    confidence: float | None = None
    source: WordSource | None = None
    code: WarningCode = WarningCode.UNSPECIFIED
    severity: WarningSeverity = WarningSeverity.WARNING


@dataclass(slots=True)
class ReversDocument:
    source_file: Path
    page_number: int
    person_name: str = ""
    person_identifier: str = ""
    organization_unit: str = ""
    equipment_items: list[EquipmentItem] = field(default_factory=list)
    closing_item_number: str = ""
    handover_date: date | None = None
    handed_over_by: str = ""
    received_by: str = ""
    warnings: list[ConversionWarning] = field(default_factory=list)
    confidence: float = 0.0

    def populated_items(self) -> list[EquipmentItem]:
        return [item for item in self.equipment_items if item.populated]
