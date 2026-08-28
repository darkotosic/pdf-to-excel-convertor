from pathlib import Path
import numpy as np
import pytesseract
from pytesseract import Output
from pdf_to_excel.models import BoundingBox, OCRWord
from pdf_to_excel.text.normalizer import normalize_text
from .tesseract_locator import locate_tesseract


class TesseractEngine:
    def __init__(self, command: Path | None = None, confidence_threshold: float = 35) -> None:
        pytesseract.pytesseract.tesseract_cmd = str(locate_tesseract(command))
        self.confidence_threshold = confidence_threshold

    def extract_words(
        self, image: np.ndarray, page_number: int, languages: tuple[str, ...]
    ) -> list[OCRWord]:
        data = pytesseract.image_to_data(
            image, lang="+".join(languages), config="--oem 3 --psm 6", output_type=Output.DICT
        )
        words = []
        for i, raw in enumerate(data["text"]):
            text, confidence = normalize_text(raw), float(data["conf"][i])
            if text and confidence >= self.confidence_threshold:
                x, y, w, h = (int(data[key][i]) for key in ("left", "top", "width", "height"))
                words.append(
                    OCRWord(text, confidence, BoundingBox(x, y, x + w, y + h), page_number)
                )
        return words
