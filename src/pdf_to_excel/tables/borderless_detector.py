from pdf_to_excel.models import ExtractedTable, SourceType, TableCell, OCRWord
from .word_clusterer import cluster_rows


def reconstruct_borderless(words: list[OCRWord], page_number: int) -> list[ExtractedTable]:
    rows = cluster_rows(words)
    if not rows:
        return []
    cells = [
        [TableCell(r, c, word.text, word.bbox, word.confidence) for c, word in enumerate(row)]
        for r, row in enumerate(rows)
    ]
    return [ExtractedTable(page_number, 1, cells, SourceType.OCR)]
