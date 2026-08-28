from pathlib import Path
import numpy as np
import pytesseract
from pytesseract import Output
from pdf_to_excel.models import BoundingBox, DocumentWord, WordSource
from pdf_to_excel.text.normalizer import normalize_text
from .tesseract_locator import locate_tesseract


class TesseractEngine:
    def __init__(self, command: Path | None = None, confidence_threshold: float = 0.35) -> None:
        pytesseract.pytesseract.tesseract_cmd = str(locate_tesseract(command))
        self.confidence_threshold = confidence_threshold

    def extract_words(
        self, image: np.ndarray, page_number: int, languages: tuple[str, ...]
        , psm: int = 6
    ) -> list[DocumentWord]:
        data = pytesseract.image_to_data(
            image, lang="+".join(languages), config=f"--oem 3 --psm {psm}", output_type=Output.DICT
        )
        words = []
        for i, raw in enumerate(data["text"]):
            text, confidence = normalize_text(raw), max(0.0, float(data["conf"][i]) / 100.0)
            if text and confidence >= self.confidence_threshold:
                x, y, w, h = (int(data[key][i]) for key in ("left", "top", "width", "height"))
                words.append(
                    DocumentWord(text, BoundingBox(x, y, x + w, y + h), confidence,
                                 page_number, WordSource.OCR)
                )
        return words
