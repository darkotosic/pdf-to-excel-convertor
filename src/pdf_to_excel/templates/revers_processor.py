from __future__ import annotations

from pathlib import Path

from pdf_to_excel.models import (
    ConversionWarning,
    DetectedGrid,
    DocumentWord,
    EquipmentItem,
    ReversDocument,
)
from pdf_to_excel.ocr.artifacts import is_ocr_table_artifact
from pdf_to_excel.tables.cell_assignment import assign_words_to_cells
from pdf_to_excel.templates.revers_footer import extract_revers_footer
from pdf_to_excel.templates.revers_metadata import extract_revers_metadata


def select_revers_equipment_grid(
    grids: list[DetectedGrid], page_width: float, page_height: float
) -> tuple[DetectedGrid | None, float]:
    """Select the broad, many-row, six-column grid typical of a REVERS form."""
    scored: list[tuple[float, DetectedGrid]] = []
    for grid in grids:
        column_score = (
            1.0 if grid.column_count == 6 else max(0.0, 1 - abs(grid.column_count - 6) / 6)
        )
        row_score = min(1.0, grid.row_count / 20)
        width_score = min(1.0, grid.bbox.width / max(1.0, page_width * 0.75))
        location_score = 1.0 if grid.bbox.center_y > page_height * 0.3 else 0.5
        score = 0.5 * column_score + 0.25 * row_score + 0.2 * width_score + 0.05 * location_score
        scored.append((score, grid))
    if not scored:
        return None, 0.0
    score, grid = max(scored, key=lambda item: item[0])
    return (grid, score) if grid.column_count == 6 and score >= 0.65 else (None, score)


def extract_revers(
    source: Path,
    page_number: int,
    grid: DetectedGrid,
    words: list[DocumentWord],
    template_confidence: float,
) -> ReversDocument:
    cells = assign_words_to_cells(grid, words)
    document = ReversDocument(source, page_number, confidence=template_confidence)
    if not cells:
        return document
    header = " ".join(cell.text for cell in cells[0]).casefold()
    expected = ("red", "oprem", "model", "kol", "serij", "inventar")
    if sum(token in header for token in expected) < 3:
        document.warnings.append(ConversionWarning("Header partially detected", page_number))
    for index, row in enumerate(cells[1:], 1):
        fields = (
            "item_number",
            "equipment_type",
            "model",
            "quantity",
            "serial_number",
            "inventory_number",
        )
        values = []
        for field_name, cell in zip(fields, row, strict=True):
            value = cell.text.strip()
            touches_border = cell.bbox is not None and any(
                abs(edge - boundary) <= 2
                for edge in (cell.bbox.x0, cell.bbox.x1)
                for boundary in grid.column_boundaries
            )
            if is_ocr_table_artifact(
                value,
                field=field_name,
                confidence=cell.confidence,
                touches_cell_border=touches_border,
            ):
                value = ""
            values.append(value)
        confidence = min(
            (cell.confidence for cell in row if cell.confidence is not None), default=1.0
        )
        document.equipment_items.append(
            EquipmentItem(
                item_number=values[0],
                equipment_type=values[1],
                model=values[2],
                quantity=values[3],
                serial_number=values[4],
                inventory_number=values[5],
                confidence=confidence,
            )
        )
    extract_revers_metadata(document, words, grid)
    extract_revers_footer(document, words, grid)
    return document
