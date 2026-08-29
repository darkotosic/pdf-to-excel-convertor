from __future__ import annotations

from datetime import date
from pathlib import Path
import re

from pdf_to_excel.models import (
    ConversionWarning,
    DetectedGrid,
    DocumentWord,
    EquipmentItem,
    ReversDocument,
)
from pdf_to_excel.ocr.artifacts import is_ocr_table_artifact
from pdf_to_excel.tables.cell_assignment import assign_words_to_cells


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
    _extract_metadata(document, words, grid)
    return document


def _extract_metadata(
    document: ReversDocument, words: list[DocumentWord], grid: DetectedGrid
) -> None:
    _extract_header_geometry(document, words, grid)
    _extract_footer_geometry(document, words, grid)


_LABEL_FRAGMENTS = ("prezime", "ime", "naziv", "organizacione", "jedinice")


def _extract_header_geometry(
    document: ReversDocument, words: list[DocumentWord], grid: DetectedGrid
) -> None:
    """Read values above their caption line, rather than treating captions as values."""
    page_height = max((word.bbox.y1 for word in words), default=grid.bbox.y1)
    band_height = max(grid.bbox.height * 0.18, page_height * 0.08)
    candidates = [
        word for word in words if grid.bbox.y0 - band_height <= word.bbox.center_y < grid.bbox.y0
    ]
    label_words = [
        word
        for word in candidates
        if any(token in word.text.casefold() for token in _LABEL_FRAGMENTS)
    ]
    if not label_words:
        return
    label_y = sum(word.bbox.center_y for word in label_words) / len(label_words)
    value_words = [
        word
        for word in candidates
        if word.bbox.center_y < label_y - max(1.0, word.bbox.height * 0.15)
        and not _is_metadata_label(word.text)
    ]
    if not value_words:
        return

    left = grid.bbox.x0
    width = grid.bbox.width
    # Metadata boxes use relative horizontal regions across REVERS revisions.
    person_words = [word for word in value_words if word.bbox.center_x < left + width * 0.48]
    identifier_words = [
        word
        for word in value_words
        if left + width * 0.48 <= word.bbox.center_x < left + width * 0.68
    ]
    organization_words = [word for word in value_words if word.bbox.center_x >= left + width * 0.68]
    document.person_name = _join_words(person_words)
    identifier = "".join(re.findall(r"\d", _join_words(identifier_words)))
    if identifier:
        document.person_identifier = identifier
    document.organization_unit = _join_words(organization_words)


def _extract_footer_geometry(
    document: ReversDocument, words: list[DocumentWord], grid: DetectedGrid
) -> None:
    footer = [word for word in words if word.bbox.center_y > grid.bbox.y1]
    lines = _word_lines(footer)
    for line in lines:
        text = _join_words(line)
        folded = text.casefold()
        if "zaklju" in folded and "broj" in folded:
            document.closing_item_number = _value_after_label(text, r"broj(?:em)?")
        elif "datum" in folded and ("predaj" in folded or "oprem" in folded):
            raw_date = _value_after_label(text, r"opreme")
            parsed = _parse_date(raw_date)
            if parsed is not None:
                document.handover_date = parsed
            elif re.search(r"\d", raw_date):
                document.warnings.append(
                    ConversionWarning(
                        "Invalid or uncertain handover date",
                        document.page_number,
                        field="handover_date",
                        value=raw_date,
                    )
                )
        elif "opremu predao" in folded:
            document.handed_over_by = _value_after_label(text, r"opremu\s+predao")
        elif "opremu primio" in folded:
            document.received_by = _value_after_label(text, r"opremu\s+primio")


def _parse_date(value: str) -> date | None:
    parts = re.search(r"(?<!\d)(\d{1,2})\s*[./|\- ]\s*(\d{1,2})\s*[./|\- ]\s*(\d{4})(?!\d)", value)
    if not parts:
        return None
    try:
        return date(int(parts.group(3)), int(parts.group(2)), int(parts.group(1)))
    except ValueError:
        return None


def _is_metadata_label(text: str) -> bool:
    folded = text.casefold().strip("() :")
    return any(fragment in folded for fragment in _LABEL_FRAGMENTS)


def _word_lines(words: list[DocumentWord]) -> list[list[DocumentWord]]:
    lines: list[list[DocumentWord]] = []
    for word in sorted(words, key=lambda item: (item.bbox.center_y, item.bbox.x0)):
        line = next(
            (
                candidate
                for candidate in reversed(lines)
                if abs(candidate[0].bbox.center_y - word.bbox.center_y)
                <= max(candidate[0].bbox.height, word.bbox.height) * 0.65
            ),
            None,
        )
        if line is None:
            lines.append([word])
        else:
            line.append(word)
    return lines


def _join_words(words: list[DocumentWord]) -> str:
    return " ".join(
        word.text.strip()
        for word in sorted(words, key=lambda item: item.bbox.x0)
        if word.text.strip()
    ).strip()


def _value_after_label(value: str, label_pattern: str) -> str:
    match = re.search(label_pattern + r"\s*[:：]?\s*", value, flags=re.IGNORECASE)
    return value[match.end() :].strip(" _|:：") if match else ""
