from dataclasses import dataclass
import fitz
from pdf_to_excel.models import PageType


@dataclass(frozen=True, slots=True)
class PageAnalysis:
    page_number: int
    character_count: int
    word_count: int
    text_coverage: float
    image_count: int
    image_coverage: float
    vector_drawing_count: int
    usable_word_ratio: float
    page_type: PageType

    @property
    def is_digital(self) -> bool:
        return self.page_type == PageType.DIGITAL


def analyze_page(page: fitz.Page) -> PageAnalysis:
    text = page.get_text("text").strip()
    words = page.get_text("words")
    page_area = max(1.0, page.rect.width * page.rect.height)
    word_area = sum(max(0.0, (w[2] - w[0]) * (w[3] - w[1])) for w in words)
    usable = sum(bool(str(w[4]).strip()) and any(ch.isalnum() for ch in str(w[4])) for w in words)
    images = page.get_images(full=True)
    image_area = 0.0
    for image in images:
        try:
            image_area += sum(rect.width * rect.height for rect in page.get_image_rects(image))
        except ValueError:
            continue
    coverage = min(1.0, word_area / page_area)
    image_coverage = min(1.0, image_area / page_area)
    usable_ratio = usable / len(words) if words else 0.0
    digital_signal = len(text) >= 20 and len(words) >= 4 and usable_ratio >= 0.55
    scan_signal = image_coverage >= 0.45
    page_type = (
        PageType.MIXED if digital_signal and scan_signal
        else PageType.DIGITAL if digital_signal
        else PageType.SCANNED
    )
    return PageAnalysis(
        page.number + 1, len(text), len(words), coverage, len(images), image_coverage,
        len(page.get_drawings()), usable_ratio, page_type,
    )
