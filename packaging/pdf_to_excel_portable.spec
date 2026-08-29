import os
from pathlib import Path

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import copy_metadata

root = Path(SPECPATH).parent
vendor = root / "vendor" / "tesseract"
icon = root / "assets" / "app.ico"
a = Analysis(
    [str(root / "app.py")], pathex=[str(root / "src")],
    datas=copy_metadata("pdf-to-excel-converter"),
    excludes=["pytest", "pytest_cov", "ruff", "mypy", "PyInstaller"], noarchive=False,
)
if vendor.is_dir():
    a.datas += Tree(str(vendor), prefix="vendor/tesseract")
if icon.is_file():
    a.datas += [(str(icon), "assets")]
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, name="PDF-to-Excel-Portable", console=False,
    icon=str(icon) if icon.is_file() else None,
    version=os.environ.get("PDF_TO_EXCEL_VERSION_FILE"),
    manifest=str(root / "packaging" / "windows.manifest"),
)
