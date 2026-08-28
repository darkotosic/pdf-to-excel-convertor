from datetime import date
from pathlib import Path

from pdf_to_excel.extraction.generic_ruled import extract_generic_ruled_tables
from pdf_to_excel.models import (
    BoundingBox,
    DetectedGrid,
    DocumentWord,
    ReversDocument,
    WordSource,
)
from pdf_to_excel.templates.revers_footer import extract_revers_footer
from pdf_to_excel.templates.revers_metadata import extract_revers_metadata


def _word(text: str, x: float, y: float, width: float = 70) -> DocumentWord:
    return DocumentWord(text, BoundingBox(x, y, x + width, y + 10), 0.95, 1, WordSource.OCR)


def test_blank_revers_captions_are_not_metadata_values() -> None:
    document = ReversDocument(Path("sanitized.pdf"), 1)
    grid = DetectedGrid(BoundingBox(10, 100, 300, 300), (100, 200, 300), (10, 155, 300))
    words = [
        _word("(prezime i ime)", 20, 70),
        _word("(naziv organizacione jedinice)", 160, 70, 130),
    ]
    extract_revers_metadata(document, words, grid)
    assert document.person_name == ""
    assert document.organization_unit == ""


def test_revers_metadata_values_above_geometric_labels() -> None:
    document = ReversDocument(Path("sanitized.pdf"), 1)
    grid = DetectedGrid(BoundingBox(10, 120, 300, 300), (120, 200, 300), (10, 155, 300))
    words = [
        _word("Ђорђе Јовановић", 20, 62, 100),
        _word("Odeljenje IKT", 165, 62, 100),
        _word("(prezime i ime)", 20, 78, 100),
        _word("(naziv organizacione jedinice)", 165, 78, 125),
    ]
    extract_revers_metadata(document, words, grid)
    assert document.person_name == "Ђорђе Јовановић"
    assert document.organization_unit == "Odeljenje IKT"


def test_revers_footer_parses_boxed_date_and_closing_number() -> None:
    document = ReversDocument(Path("sanitized.pdf"), 1)
    grid = DetectedGrid(BoundingBox(10, 20, 300, 200), (20, 200), (10, 300))
    words = [
        _word("Zaključno sa rednim brojem: 3.", 10, 220, 180),
        _word("Datum predaje opreme 01 | 12 | 2026", 10, 240, 220),
        _word("OPREMU PREDAO: Petar Petrović", 10, 260, 190),
        _word("OPREMU PRIMIO: Milan Milić", 10, 280, 190),
    ]
    extract_revers_footer(document, words, grid)
    assert document.closing_item_number == "3."
    assert document.handover_date == date(2026, 12, 1)
    assert document.handed_over_by == "Petar Petrović"
    assert document.received_by == "Milan Milić"


def test_generic_scanned_ruled_table_reconstruction() -> None:
    grid = DetectedGrid(
        BoundingBox(0, 0, 300, 120),
        (0, 30, 60, 90, 120),
        (0, 100, 200, 300),
    )
    rows = [
        ("Name", "City", "Phone"),
        ("Marko Marković", "Ruma", "0641234567"),
        ("Jovan Jovanović", "Šabac", "0631234567"),
        ("Ђорђе Петровић", "Чачак", "0621234567"),
    ]
    words = [
        _word(value, column * 100 + 8, row * 30 + 8, 80)
        for row, values in enumerate(rows)
        for column, value in enumerate(values)
    ]
    tables = extract_generic_ruled_tables([grid], words, 1)
    assert len(tables) == 1
    assert len(tables[0].rows) == 4
    assert len(tables[0].rows[0]) == 3
    assert [cell.text for cell in tables[0].rows[0]] == ["Name", "City", "Phone"]
    assert tables[0].rows[3][0].text == "Ђорђе Петровић"
    assert tables[0].rows[1][2].text == "0641234567"
