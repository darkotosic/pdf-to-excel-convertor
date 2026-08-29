"""Machine-readable diagnostics for release bundle verification."""

from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import subprocess
import sys

from pdf_to_excel.ocr.tesseract_engine import configure_tesseract
from pdf_to_excel.utils.paths import get_resource_path

REQUIRED_LANGUAGES = {"eng", "srp", "srp_latn", "osd"}


def _project_version() -> str:
    try:
        return version("pdf-to-excel-converter")
    except PackageNotFoundError:
        return "unknown"


def run_self_test(output: Path | None) -> int:
    checks: dict[str, object] = {}
    failures: list[str] = []
    for module in ("PySide6", "fitz", "cv2", "pdfplumber", "openpyxl"):
        try:
            __import__(module)
            checks[module] = True
        except Exception as error:  # diagnostics must report every failed component
            checks[module] = False
            failures.append(f"{module}: {error}")
    try:
        executable = configure_tesseract()
        completed = subprocess.run(
            [executable, "--version"], capture_output=True, text=True, timeout=30, check=True
        )
        languages_result = subprocess.run(
            [executable, "--list-langs"], capture_output=True, text=True, timeout=30, check=True
        )
        languages = set(languages_result.stdout.splitlines())
        missing = sorted(REQUIRED_LANGUAGES - languages)
        checks.update(
            tesseract_executable=str(executable),
            tesseract_version=completed.stdout.splitlines()[0],
            ocr_languages=sorted(languages),
        )
        if missing:
            failures.append(f"Missing OCR languages: {', '.join(missing)}")
    except Exception as error:
        failures.append(f"Tesseract: {error}")
    report = {
        "success": not failures,
        "frozen": bool(getattr(sys, "frozen", False)),
        "version": _project_version(),
        "resource_root": str(get_resource_path(".").resolve()),
        "checks": checks,
        "failures": failures,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0 if not failures else 1
