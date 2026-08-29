from pathlib import Path
import pdfplumber
from pdf_to_excel.models import ExtractedTable, SourceType, TableCell
from pdf_to_excel.text.normalizer import normalize_text


def extract_digital_tables(path: Path, page_number: int) -> list[ExtractedTable]:
    with pdfplumber.open(path) as document:
        page = document.pages[page_number - 1]
        raw_tables: list[list[list[str | None]]] = page.extract_tables() or []
        if not raw_tables:
            words = page.extract_words() or []
            raw_tables = [_words_to_rows(words)] if words else []
        result = []
        for table_index, raw in enumerate(raw_tables, 1):
            rows = [
                [TableCell(r, c, normalize_text(value or "")) for c, value in enumerate(row)]
                for r, row in enumerate(raw)
                if row
            ]
            if rows:
                result.append(ExtractedTable(page_number, table_index, rows, SourceType.DIGITAL))
        return result


def _words_to_rows(words: list[dict[str, object]]) -> list[list[str | None]]:
    lines: list[list[dict[str, object]]] = []

    def coordinate(word: dict[str, object], key: str) -> float:
        value = word[key]
        if not isinstance(value, (str, int, float)):
            raise TypeError(f"Invalid PDF word coordinate: {value!r}")
        return float(value)

    for word in sorted(words, key=lambda w: (coordinate(w, "top"), coordinate(w, "x0"))):
        line = next(
            (
                line
                for line in lines
                if abs(coordinate(line[0], "top") - coordinate(word, "top")) <= 4
            ),
            None,
        )
        if line is None:
            line = []
            lines.append(line)
        line.append(word)
    return [[str(word["text"]) for word in line] for line in lines]
