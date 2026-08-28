from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from .geometry import BoundingBox


class SourceType(StrEnum):
    DIGITAL = "digital"
    OCR = "ocr"


@dataclass(slots=True)
class TableCell:
    row: int
    column: int
    text: str
    bbox: BoundingBox | None = None
    confidence: float | None = None
    rowspan: int = 1
    colspan: int = 1


@dataclass(slots=True)
class ExtractedTable:
    page_number: int
    table_index: int
    rows: list[list[TableCell]]
    source_type: SourceType
