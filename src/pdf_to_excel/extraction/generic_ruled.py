from __future__ import annotations

from pdf_to_excel.models import DetectedGrid, DocumentWord, ExtractedTable, SourceType, TableCell
from pdf_to_excel.tables.cell_assignment import assign_words_to_cells


def extract_generic_ruled_tables(
    grids: list[DetectedGrid],
    words: list[DocumentWord],
    page_number: int,
) -> list[ExtractedTable]:
    """Reconstruct credible ruled tables from raster geometry and OCR words.

    Geometry is deliberately detected on the image before its rules are removed
    for OCR.  This function therefore only scores and combines existing results;
    it does not introduce a second, template-specific image pipeline.
    """
    candidates: list[tuple[float, DetectedGrid, list[list[TableCell]]]] = []
    for grid in grids:
        cells = assign_words_to_cells(grid, words)
        score = _candidate_score(grid, cells)
        if score >= 0.55:
            candidates.append((score, grid, cells))

    # A detector can return the same table plus a nested fragment. Keep the
    # strongest/largest candidate and retain genuinely separate tables.
    accepted: list[tuple[DetectedGrid, list[list[TableCell]]]] = []
    for _, grid, cells in sorted(candidates, key=lambda item: (-item[0], -item[1].bbox.width)):
        if any(grid.bbox.overlap_ratio(existing.bbox) > 0.8 for existing, _ in accepted):
            continue
        accepted.append((grid, cells))

    return [
        ExtractedTable(page_number, index, cells, SourceType.OCR)
        for index, (_, cells) in enumerate(accepted, 1)
    ]


def _candidate_score(grid: DetectedGrid, cells: list[list[TableCell]]) -> float:
    if grid.row_count < 2 or grid.column_count < 2 or not cells:
        return 0.0
    total = grid.row_count * grid.column_count
    populated = sum(bool(cell.text.strip()) for row in cells for cell in row)
    text_density = populated / max(1, total)
    structure = min(1.0, grid.row_count / 4) * min(1.0, grid.column_count / 3)
    # Requiring text in more than one row rejects signatures and decorative boxes.
    populated_rows = sum(any(cell.text.strip() for cell in row) for row in cells)
    repetition = min(1.0, populated_rows / max(2, grid.row_count))
    return 0.35 * structure + 0.4 * text_density + 0.25 * repetition
