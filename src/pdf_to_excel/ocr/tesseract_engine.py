from pathlib import Path
import numpy as np
import pytesseract
from pytesseract import Output
from pdf_to_excel.exceptions import MissingOcrLanguageError, OcrTimeoutError
from pdf_to_excel.models import BoundingBox, DocumentWord, WordSource
from pdf_to_excel.text.normalizer import normalize_text
from .tesseract_locator import locate_tesseract


class TesseractEngine:
    def __init__(
        self,
        command: Path | None = None,
        confidence_threshold: float = 0.35,
        timeout_seconds: float = 120,
    ) -> None:
        pytesseract.pytesseract.tesseract_cmd = str(locate_tesseract(command))
        self.confidence_threshold = confidence_threshold
        self.timeout_seconds = timeout_seconds

    def get_available_languages(self) -> set[str]:
        """Return installed trained-data names using the configured executable."""
        return set(pytesseract.get_languages(config=""))

    def validate_languages(self, languages: tuple[str, ...], *, require_osd: bool = False) -> None:
        required = set(languages)
        if require_osd:
            required.add("osd")
        missing = sorted(required - self.get_available_languages())
        if missing:
            friendly = {
                "srp": "Serbian Cyrillic OCR language is not available.",
                "srp_latn": "Serbian Latin OCR language is not available.",
                "eng": "English OCR language is not available.",
                "osd": "OCR orientation data is not available.",
            }
            details = " ".join(
                friendly.get(item, f"OCR language '{item}' is not available.") for item in missing
            )
            raise MissingOcrLanguageError(details)

    def extract_words(
        self, image: np.ndarray, page_number: int, languages: tuple[str, ...], psm: int = 6
    ) -> list[DocumentWord]:
        try:
            data = pytesseract.image_to_data(
                image,
                lang="+".join(languages),
                config=f"--oem 3 --psm {psm}",
                output_type=Output.DICT,
                timeout=self.timeout_seconds,
            )
        except RuntimeError as error:
            if "timeout" in str(error).casefold():
                raise OcrTimeoutError(
                    f"OCR exceeded its {self.timeout_seconds:g} second deadline."
                ) from error
            raise
        words = []
        for i, raw in enumerate(data["text"]):
            text, confidence = normalize_text(raw), max(0.0, float(data["conf"][i]) / 100.0)
            if text and confidence >= self.confidence_threshold:
                x, y, w, h = (int(data[key][i]) for key in ("left", "top", "width", "height"))
                words.append(
                    DocumentWord(
                        text,
                        BoundingBox(x, y, x + w, y + h),
                        confidence,
                        page_number,
                        WordSource.OCR,
                    )
                )
        return words
