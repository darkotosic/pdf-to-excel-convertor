from pathlib import Path

import cv2
import numpy as np

from pdf_to_excel.excel.exporter import available_output_path
from pdf_to_excel.models import BoundingBox, DetectedLine, EquipmentItem, OCRWord
from pdf_to_excel.pdf.visibility_validator import has_visible_foreground
from pdf_to_excel.tables.grid_detector import cell_boxes, detect_grids
from pdf_to_excel.tables.line_detector import detect_ruled_lines, merge_collinear
from pdf_to_excel.tables.word_clusterer import reconstruct_cell_text
from pdf_to_excel.templates import detect_template, normalize_revers_text


def test_line_merging_and_six_column_grid() -> None:
    horizontal = [DetectedLine(0, y, 600, y) for y in (0, 30, 60)]
    vertical = [DetectedLine(x, 0, x, 60) for x in (0, 50, 230, 350, 400, 500, 600)]
    grid = detect_grids(horizontal, vertical)[0]
    assert grid.column_count == 6
    assert len(cell_boxes(grid)) == 2
    assert len(merge_collinear([DetectedLine(0, 10, 40, 10), DetectedLine(42, 11, 80, 11)])) == 1


def test_opencv_rule_detection() -> None:
    image = np.full((180, 360), 255, np.uint8)
    for y in (20, 80, 140):
        cv2.line(image, (10, y), (350, y), 0, 2)
    for x in (10, 60, 120, 180, 240, 300, 350):
        cv2.line(image, (x, 20), (x, 140), 0, 2)
    horizontal, vertical, _, _ = detect_ruled_lines(image)
    assert len(horizontal) >= 3
    assert len(vertical) >= 7
    assert detect_grids(horizontal, vertical)[0].column_count == 6


def test_revers_detection_and_ocr_header_normalization() -> None:
    text = "REVERS Red.\nbroj Vrsta računarske opreme Model Kol Serijski broj Inventar\nski broj OPREMU PRIMIO"
    assert normalize_revers_text(text).find("inventarski broj") >= 0
    match = detect_template(text)
    assert match is not None
    assert match.name == "REVERS"


def test_multiline_reconstruction_and_empty_item() -> None:
    words = [
        OCRWord("HAC-HFIW1200R-", 0.9, BoundingBox(0, 0, 40, 10), 1),
        OCRWord("Z-IRE6-A-2712", 0.9, BoundingBox(0, 12, 40, 22), 1),
    ]
    assert reconstruct_cell_text(words) == "HAC-HFIW1200R-Z-IRE6-A-2712"
    assert not EquipmentItem(item_number="8").populated


def test_visibility_rejects_blank_and_accepts_glyph() -> None:
    blank = np.full((50, 50), 255, np.uint8)
    assert not has_visible_foreground(blank, BoundingBox(5, 5, 45, 45))
    cv2.putText(blank, "M", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, 0, 2)
    assert has_visible_foreground(blank, BoundingBox(5, 5, 45, 45))


def test_output_collision(tmp_path: Path) -> None:
    target = tmp_path / "revers.xlsx"
    target.touch()
    assert available_output_path(target).name == "revers (1).xlsx"
