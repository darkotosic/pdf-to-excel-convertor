"""Geometry-first extraction for non-template scanned ruled tables."""

from __future__ import annotations

from pdf_to_excel.models import DetectedGrid, DocumentWord, ExtractedTable, SourceType
from pdf_to_excel.tables.cell_assignment import assign_words_to_cells


def score_grid_candidate(
    grid: DetectedGrid,
    words: list[DocumentWord],
    page_width: float,
    page_height: float,
) -> float:
    """Score a ruled grid while rejecting decorative and signature boxes.

    Line continuity is already enforced by ``detect_grids``.  This second stage
    requires repeated rows/columns, useful page area, and text assigned to more
    than a single cell.
    """
    if grid.row_count < 2 or grid.column_count < 2:
        return 0.0
    page_area = max(1.0, page_width * page_height)
    area_ratio = grid.bbox.width * grid.bbox.height / page_area
    if area_ratio < 0.01:
        return 0.0
    cells = assign_words_to_cells(grid, words)
    populated = sum(bool(cell.text.strip()) for row in cells for cell in row)
    total = max(1, grid.row_count * grid.column_count)
    occupied_rows = sum(any(cell.text.strip() for cell in row) for row in cells)
    density = populated / total
    row_coverage = occupied_rows / grid.row_count
    structure = min(1.0, grid.row_count / 4) * min(1.0, grid.column_count / 3)
    area = min(1.0, area_ratio / 0.08)
    return 0.30 * structure + 0.25 * area + 0.25 * density + 0.20 * row_coverage


def extract_generic_ruled_tables(
    grids: list[DetectedGrid],
    words: list[DocumentWord],
    page_number: int,
    page_width: float,
    page_height: float,
    minimum_score: float = 0.45,
) -> list[ExtractedTable]:
    """Return every credible generic grid in deterministic reading order."""
    accepted = [
        grid
        for grid in grids
        if score_grid_candidate(grid, words, page_width, page_height) >= minimum_score
    ]
    accepted.sort(key=lambda grid: (grid.bbox.y0, grid.bbox.x0))
    return [
        ExtractedTable(
            page_number,
            index,
            assign_words_to_cells(grid, words),
            SourceType.OCR,
        )
        for index, grid in enumerate(accepted, 1)
    ]
