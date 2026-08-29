from pathlib import Path
import sys
from unittest.mock import patch

import pytest

from pdf_to_excel.ocr.tesseract_engine import configure_tesseract
from pdf_to_excel.ocr.tesseract_locator import locate_tesseract
from pdf_to_excel.utils.paths import get_application_root, get_resource_path


def _executable(root: Path) -> Path:
    executable = root / "vendor" / "tesseract" / "tesseract.exe"
    executable.parent.mkdir(parents=True)
    executable.touch()
    return executable


def test_normal_application_root_is_repository() -> None:
    with patch.object(sys, "frozen", False, create=True):
        assert (get_application_root() / "pyproject.toml").is_file()


def test_frozen_application_root_uses_executable(tmp_path: Path) -> None:
    executable = tmp_path / "putanja sa č ć ž š đ" / "PDF-to-Excel.exe"
    with (
        patch.object(sys, "frozen", True, create=True),
        patch.object(sys, "executable", str(executable)),
    ):
        assert get_application_root() == executable.parent.resolve()


def test_meipass_resource_lookup_supports_unicode(tmp_path: Path) -> None:
    bundle = tmp_path / "ресурси čćžšđ"
    with patch.object(sys, "_MEIPASS", str(bundle), create=True):
        assert get_resource_path("vendor/tesseract") == bundle / "vendor/tesseract"


@pytest.mark.parametrize("override", ["configured", "environment"])
def test_explicit_override_precedes_bundle(tmp_path: Path, override: str) -> None:
    bundle = _executable(tmp_path / "bundle")
    external = tmp_path / "external tesseract.exe"
    external.touch()
    configured = external if override == "configured" else None
    environment = str(external) if override == "environment" else None
    with (
        patch("pdf_to_excel.ocr.tesseract_locator.get_resource_path", return_value=bundle),
        patch.dict("os.environ", {"TESSERACT_CMD": environment} if environment else {}, clear=True),
        patch("pdf_to_excel.ocr.tesseract_locator.shutil.which", return_value=None),
    ):
        assert locate_tesseract(configured) == external


def test_bundle_precedes_path_and_configures_tessdata(tmp_path: Path) -> None:
    bundled = _executable(tmp_path / "bundle")
    (bundled.parent / "tessdata").mkdir()
    path_executable = tmp_path / "PATH" / "tesseract.exe"
    path_executable.parent.mkdir()
    path_executable.touch()
    with (
        patch("pdf_to_excel.ocr.tesseract_locator.get_resource_path", return_value=bundled),
        patch.dict("os.environ", {}, clear=True),
        patch("pdf_to_excel.ocr.tesseract_locator.shutil.which", return_value=str(path_executable)),
    ):
        assert configure_tesseract() == bundled
        assert Path(__import__("os").environ["TESSDATA_PREFIX"]) == bundled.parent / "tessdata"
