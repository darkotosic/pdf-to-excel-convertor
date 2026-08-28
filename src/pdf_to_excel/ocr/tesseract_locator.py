import os
from pathlib import Path
import shutil
from pdf_to_excel.exceptions import DependencyError


def locate_tesseract(configured: Path | None = None) -> Path:
    candidates = [
        configured,
        Path(os.environ["TESSERACT_CMD"]) if os.getenv("TESSERACT_CMD") else None,
    ]
    found = shutil.which("tesseract")
    candidates.extend(
        [
            Path(found) if found else None,
            Path.cwd() / "vendor/tesseract/tesseract.exe",
            Path(os.environ.get("ProgramFiles", "C:/Program Files"))
            / "Tesseract-OCR/tesseract.exe",
        ]
    )
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise DependencyError("Tesseract OCR was not found. Install Tesseract 5 or configure its path.")
