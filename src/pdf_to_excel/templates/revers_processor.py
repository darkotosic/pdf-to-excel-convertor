from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from pdf_to_excel.models import (ConversionWarning, DetectedGrid, DocumentWord,
                                 EquipmentItem, ReversDocument)
from pdf_to_excel.ocr.artifacts import is_ocr_table_artifact
from pdf_to_excel.tables.cell_assignment import assign_words_to_cells


def select_revers_equipment_grid(grids: list[DetectedGrid], page_width: float,
                                 page_height: float) -> tuple[DetectedGrid | None, float]:
    """Select the broad, many-row, six-column grid typical of a REVERS form."""
    scored: list[tuple[float, DetectedGrid]] = []
    for grid in grids:
        column_score = 1.0 if grid.column_count == 6 else max(0.0, 1 - abs(grid.column_count - 6) / 6)
        row_score = min(1.0, grid.row_count / 20)
        width_score = min(1.0, grid.bbox.width / max(1.0, page_width * 0.75))
        location_score = 1.0 if grid.bbox.center_y > page_height * 0.3 else 0.5
        score = .5 * column_score + .25 * row_score + .2 * width_score + .05 * location_score
        scored.append((score, grid))
    if not scored:
        return None, 0.0
    score, grid = max(scored, key=lambda item: item[0])
    return (grid, score) if grid.column_count == 6 and score >= .65 else (None, score)


def extract_revers(source: Path, page_number: int, grid: DetectedGrid,
                   words: list[DocumentWord], template_confidence: float) -> ReversDocument:
    cells = assign_words_to_cells(grid, words)
    document = ReversDocument(source, page_number, confidence=template_confidence)
    if not cells:
        return document
    header = " ".join(cell.text for cell in cells[0]).casefold()
    expected = ("red", "oprem", "model", "kol", "serij", "inventar")
    if sum(token in header for token in expected) < 3:
        document.warnings.append(ConversionWarning("Header partially detected", page_number))
    for index, row in enumerate(cells[1:], 1):
        fields = ("item_number", "equipment_type", "model", "quantity",
                  "serial_number", "inventory_number")
        values = []
        for field_name, cell in zip(fields, row, strict=True):
            value = cell.text.strip()
            touches_border = cell.bbox is not None and any(
                abs(edge - boundary) <= 2
                for edge in (cell.bbox.x0, cell.bbox.x1)
                for boundary in grid.column_boundaries)
            if is_ocr_table_artifact(
                value, field=field_name, confidence=cell.confidence,
                touches_cell_border=touches_border,
            ):
                value = ""
            values.append(value)
        confidence = min((cell.confidence for cell in row if cell.confidence is not None), default=1.0)
        document.equipment_items.append(EquipmentItem(
            item_number=values[0], equipment_type=values[1], model=values[2],
            quantity=values[3], serial_number=values[4], inventory_number=values[5],
            confidence=confidence,
        ))
    _extract_metadata(document, words, grid)
    return document


def _extract_metadata(document: ReversDocument, words: list[DocumentWord], grid: DetectedGrid) -> None:
    # Preserve reading order outside the equipment table; labels vary across revisions.
    top = sorted((word for word in words if word.bbox.y1 < grid.bbox.y0),
                 key=lambda word: (word.bbox.y0, word.bbox.x0))
    lines: dict[int, list[str]] = {}
    for word in top:
        lines.setdefault(round(word.bbox.center_y / 5), []).append(word.text)
    text_lines = [" ".join(parts) for parts in lines.values()]
    for line in text_lines:
        folded = line.casefold()
        value = re.split(r"[:：]", line, maxsplit=1)[-1].strip()
        if "jmbg" in folded or "identifik" in folded:
            document.person_identifier = re.sub(r"\D", "", value)
        elif "organizacion" in folded or "odeljenje" in folded:
            document.organization_unit = value
        elif "ime" in folded or "zaposlen" in folded:
            document.person_name = value
    footer = " ".join(word.text for word in sorted(words, key=lambda w: (w.bbox.y0, w.bbox.x0))
                      if word.bbox.y0 > grid.bbox.y1)
    match = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", footer)
    if match:
        try:
            document.handover_date = datetime.strptime(".".join(match.groups()), "%d.%m.%Y").date()
        except ValueError:
            document.warnings.append(ConversionWarning("Invalid handover date", document.page_number,
                                                        field="handover_date", value=match.group(0)))
