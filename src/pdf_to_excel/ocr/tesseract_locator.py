import os
from pathlib import Path
import shutil
from pdf_to_excel.exceptions import TesseractNotFoundError
from pdf_to_excel.utils.paths import get_resource_path


def locate_tesseract(configured: Path | None = None) -> Path:
    candidates = [
        configured,
        Path(os.environ["TESSERACT_CMD"]) if os.getenv("TESSERACT_CMD") else None,
    ]
    found = shutil.which("tesseract")
    candidates.extend(
        [
            Path(found) if found else None,
            get_resource_path("vendor/tesseract/tesseract.exe"),
            Path(os.environ.get("ProgramFiles", "C:/Program Files"))
            / "Tesseract-OCR/tesseract.exe",
        ]
    )
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise TesseractNotFoundError(
        "Tesseract OCR was not found. Reinstall the application or configure its path."
    )
