from pdf_to_excel.models import ExtractedTable, OCRWord
from .borderless_detector import reconstruct_borderless


def reconstruct(words: list[OCRWord], page_number: int) -> list[ExtractedTable]:
    return reconstruct_borderless(words, page_number)
