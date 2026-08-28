# PDF to Excel Converter

An offline Windows 10/11 desktop application that extracts tables from digital,
scanned, and mixed PDFs into genuine Excel workbooks. Serbian Cyrillic, Serbian
Latin, English, and mixed-script documents are preserved as Unicode.

## Features

- Chooses native extraction or local Tesseract OCR independently for every page.
- Reconstructs ruled tables and heuristically clusters borderless rows/columns.
- Protects Excel users from formula injection and infers safe numeric/date values.
- Page selection, progress reporting, cancellation, drag-and-drop, and local logs.
- No document content or telemetry ever leaves the computer.

## Install and run

Install Python 3.12 x64 and Tesseract 5 with `srp`, `srp_latn`, and `eng` data.
Then run:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Tesseract is located from the configured path, `TESSERACT_CMD`, `PATH`, the
vendored directory, or common Windows install locations. Settings are stored in
the platform-specific user configuration directory.

## Development

```powershell
pip install -r requirements-dev.txt
./scripts/check.ps1
./scripts/test.ps1
./scripts/build_windows.ps1
```

The build script creates a one-folder PyInstaller distribution. Tesseract itself
is not redistributed; see `vendor/tesseract/README.md` for optional offline
bundling instructions and licensing obligations. The Inno Setup definition under
`installer/` creates a Windows installer.

## Architecture

`ConversionPipeline` analyzes each selected page. Pages with useful selectable
text use pdfplumber; image pages are rendered by PyMuPDF, preprocessed with
OpenCV, and recognized by Tesseract. Both paths produce the same table model,
which is cleaned and exported with openpyxl. The GUI invokes this pipeline on a
worker thread, keeping all processing local.

## Limitations

PDF table reconstruction is heuristic. Complex nested tables, handwriting,
damaged scans, and merged cells may require manual correction. OCR quality is
bounded by scan resolution and installed language data.

## License

MIT. Third-party components retain their own licenses.
