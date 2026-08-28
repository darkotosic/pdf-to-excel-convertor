from pathlib import Path

import cv2
import numpy as np

from pdf_to_excel.excel.exporter import available_output_path
from pdf_to_excel.models import (
    BoundingBox,
    DetectedLine,
    DocumentWord,
    EquipmentItem,
    OCRWord,
    WordSource,
)
from pdf_to_excel.ocr.artifacts import is_ocr_table_artifact
from pdf_to_excel.ocr.deskew import estimate_skew_angle
from pdf_to_excel.ocr.preprocessing import remove_detected_table_lines
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


def test_ocr_table_artifacts_are_field_aware() -> None:
    for value in ("|", "||", "_", "__", "__|", "|I"):
        assert is_ocr_table_artifact(value, field="model", confidence=0.2, touches_cell_border=True)
    assert not is_ocr_table_artifact("-12", field="quantity", confidence=0.4)
    assert not is_ocr_table_artifact("AB-12", field="serial_number", confidence=0.4)


def test_line_removal_preserves_text() -> None:
    image = np.full((100, 240), 255, np.uint8)
    cv2.line(image, (5, 50), (235, 50), 0, 2)
    cv2.putText(image, "Model", (70, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 0, 2)
    _, _, horizontal_mask, vertical_mask = detect_ruled_lines(image)
    cleaned = remove_detected_table_lines(image, horizontal_mask, vertical_mask)
    assert cleaned[50, 20] > 240
    assert np.count_nonzero(cleaned[15:40, 65:145] < 128) > 10


def test_deskew_uses_horizontal_rules() -> None:
    image = np.full((220, 420), 255, np.uint8)
    for y in (50, 100, 150):
        cv2.line(image, (20, y), (400, y + 13), 0, 2)
    assert 1.0 < estimate_skew_angle(image) < 3.0


def test_generic_grid_scoring_rejects_decorative_box() -> None:
    from pdf_to_excel.extraction.generic_ruled import score_grid_candidate
    from pdf_to_excel.models import DetectedGrid

    decorative = DetectedGrid(BoundingBox(10, 10, 30, 30), (10, 30), (10, 30))
    table = DetectedGrid(
        BoundingBox(10, 10, 310, 170),
        (10, 50, 90, 130, 170),
        (10, 110, 210, 310),
    )
    words = [
        DocumentWord(
            f"value-{row}-{column}",
            BoundingBox(20 + column * 100, 20 + row * 40, 90 + column * 100, 40 + row * 40),
            0.9,
            1,
            WordSource.OCR,
        )
        for row in range(4)
        for column in range(3)
    ]

    assert score_grid_candidate(decorative, words, 400, 300) == 0
    assert score_grid_candidate(table, words, 400, 300) >= 0.45
