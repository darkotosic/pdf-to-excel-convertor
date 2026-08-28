from dataclasses import dataclass
import fitz
from pdf_to_excel.constants import MIN_DIGITAL_CHARACTERS


@dataclass(frozen=True, slots=True)
class PageAnalysis:
    page_number: int
    is_digital: bool
    character_count: int


def analyze_page(page: fitz.Page) -> PageAnalysis:
    text = page.get_text("text").strip()
    return PageAnalysis(page.number + 1, len(text) >= MIN_DIGITAL_CHARACTERS, len(text))
