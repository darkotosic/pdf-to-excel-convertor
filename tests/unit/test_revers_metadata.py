from datetime import date
from pathlib import Path

from pdf_to_excel.models import BoundingBox, DetectedGrid, DocumentWord, ReversDocument, WordSource
from pdf_to_excel.templates.revers_processor import _extract_metadata, _parse_date


def _word(text: str, x: float, y: float) -> DocumentWord:
    return DocumentWord(
        text, BoundingBox(x, y, x + max(8, len(text) * 5), y + 10), 1.0, 1, WordSource.NATIVE
    )


def test_blank_metadata_captions_are_not_values() -> None:
    grid = DetectedGrid(BoundingBox(10, 200, 610, 700), (200, 220), (10, 110))
    document = ReversDocument(Path("blank.pdf"), 1)
    words = [_word("(prezime i ime)", 30, 180), _word("(naziv organizacione jedinice)", 420, 180)]

    _extract_metadata(document, words, grid)

    assert document.person_name == ""
    assert document.person_identifier == ""
    assert document.organization_unit == ""


def test_metadata_uses_relative_value_regions_and_preserves_identifier() -> None:
    grid = DetectedGrid(BoundingBox(10, 200, 610, 700), (200, 220), (10, 110))
    document = ReversDocument(Path("filled.pdf"), 1)
    words = [
        _word("Ђорђе", 30, 160),
        _word("Јовановић", 80, 160),
        _word("0112979710162", 310, 160),
        _word("Odeljenje", 430, 160),
        _word("IKT", 500, 160),
        _word("(prezime i ime)", 30, 180),
        _word("(naziv organizacione jedinice)", 420, 180),
    ]

    _extract_metadata(document, words, grid)

    assert document.person_name == "Ђорђе Јовановић"
    assert document.person_identifier == "0112979710162"
    assert document.organization_unit == "Odeljenje IKT"


def test_date_parser_supports_separate_boxes_and_validates() -> None:
    assert _parse_date("28 | 08 | 2026") == date(2026, 8, 28)
    assert _parse_date("31.02.2026") is None
