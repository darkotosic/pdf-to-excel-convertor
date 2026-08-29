from __future__ import annotations

from statistics import median

from pdf_to_excel.models import DetectedGrid, DocumentWord, TableCell
from pdf_to_excel.tables.grid_detector import cell_boxes
from pdf_to_excel.templates.revers import normalize_revers_text


def assign_words_to_cells(grid: DetectedGrid, words: list[DocumentWord]) -> list[list[TableCell]]:
    """Assign top-left-coordinate words to geometric cells.

    Center containment is authoritative. Boundary-crossing words fall back to
    greatest bbox overlap. Words with no intersection with the grid are ignored.
    """
    boxes = cell_boxes(grid)
    buckets: list[list[list[DocumentWord]]] = [
        [[] for _ in range(grid.column_count)] for _ in range(grid.row_count)
    ]
    for word in words:
        if word.bbox.intersection(grid.bbox) is None:
            continue
        candidates: list[tuple[float, int, int]] = []
        for row, row_boxes in enumerate(boxes):
            for column, box in enumerate(row_boxes):
                centered = (
                    box.x0 <= word.bbox.center_x <= box.x1
                    and box.y0 <= word.bbox.center_y <= box.y1
                )
                overlap = box.overlap_ratio(word.bbox)
                if centered or overlap:
                    candidates.append((2.0 + overlap if centered else overlap, row, column))
        if candidates:
            _, row, column = max(candidates)
            buckets[row][column].append(word)

    heights = [word.bbox.height for word in words if word.bbox.height > 0]
    tolerance = max(1.0, median(heights) * 0.55) if heights else 2.0
    result: list[list[TableCell]] = []
    for row, row_boxes in enumerate(boxes):
        cells: list[TableCell] = []
        for column, box in enumerate(row_boxes):
            cell_words = _reading_order(buckets[row][column], tolerance)
            text = reconstruct_cell_text(cell_words, tolerance)
            confidence = min((word.confidence for word in cell_words), default=None)
            cells.append(TableCell(row, column, text, box, confidence))
        result.append(cells)
    return result


def _reading_order(words: list[DocumentWord], tolerance: float) -> list[DocumentWord]:
    lines: list[list[DocumentWord]] = []
    for word in sorted(words, key=lambda item: (item.bbox.center_y, item.bbox.x0)):
        line = next(
            (
                line
                for line in lines
                if abs(line[0].bbox.center_y - word.bbox.center_y) <= tolerance
            ),
            None,
        )
        if line is None:
            lines.append([word])
        else:
            line.append(word)
    return [word for line in lines for word in sorted(line, key=lambda item: item.bbox.x0)]


def reconstruct_cell_text(words: list[DocumentWord], tolerance: float = 2.0) -> str:
    if not words:
        return ""
    lines: list[list[DocumentWord]] = []
    for word in _reading_order(words, tolerance):
        if not lines or abs(lines[-1][0].bbox.center_y - word.bbox.center_y) > tolerance:
            lines.append([word])
        else:
            lines[-1].append(word)
    texts = [" ".join(word.text for word in line).strip() for line in lines]
    value = ""
    for text in texts:
        value = value + text if value.endswith("-") else " ".join(filter(None, (value, text)))
    normalized = normalize_revers_text(value)
    if normalized == "inventarski broj":
        return "Inventarski broj"
    if normalized == "red. broj":
        return "Red. broj"
    return value.strip()
