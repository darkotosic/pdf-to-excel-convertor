import os
from pathlib import Path

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import copy_metadata

root = Path(SPECPATH).parent
version_file = os.environ.get("PDF_TO_EXCEL_VERSION_FILE")
icon_file = root / "assets" / "app.ico"
manifest_file = root / "packaging" / "windows.manifest"
vendor = root / "vendor" / "tesseract"

a = Analysis(
    [str(root / "app.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=copy_metadata("pdf-to-excel-converter"),
    hiddenimports=[],
    excludes=["pytest", "pytest_cov", "ruff", "mypy", "PyInstaller"],
    noarchive=False,
)
if vendor.is_dir():
    a.datas += Tree(str(vendor), prefix="vendor/tesseract")
if icon_file.is_file():
    a.datas += [(str(icon_file), "assets")]
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PDF-to-Excel",
    console=False,
    icon=str(icon_file) if icon_file.is_file() else None,
    version=version_file,
    manifest=str(manifest_file),
)
coll = COLLECT(exe, a.binaries, a.datas, name="PDF-to-Excel")
