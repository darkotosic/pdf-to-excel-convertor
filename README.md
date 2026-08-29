# PDF to Excel Converter

An entirely offline Windows 10/11 x64 desktop application that extracts tables
from digital, scanned, and mixed PDFs into genuine Excel workbooks. Serbian
Cyrillic, Serbian Latin, English, and mixed-script documents remain Unicode.

## Features and architecture

- Chooses native extraction or local Tesseract OCR independently per page.
- Reconstructs ruled and borderless tables without changing the existing engine.
- Protects Excel users from formula injection and infers safe values.
- Runs the PySide6 GUI and conversion pipeline locally, with no telemetry.
- Stores settings and rotating logs in normal per-user platform directories.

## End-user release

Normal users receive `release\PDF-to-Excel-Setup-{VERSION}-x64.exe`. It installs
the windowed PyInstaller onedir application and a verified private Tesseract 5
runtime. A clean machine needs **no Python, pip, Tesseract, developer tools, or
runtime Internet access**. The installer is per-user and the application runs
without administrator privileges.

The secondary `PDF-to-Excel-{VERSION}-x64.zip` contains the same onedir bundle
for diagnostics and managed deployment.

## Windows development flow

Use 64-bit Python 3.12 and a trusted Tesseract 5 Windows installation containing
`eng`, `srp`, `srp_latn`, and `osd`:

```powershell
.\scripts\setup_dev.ps1
.\scripts\prepare_tesseract.ps1
.\scripts\quality_gate.ps1
```

Pass a non-default trusted source with
`.\scripts\prepare_tesseract.ps1 -Source "C:\Program Files\Tesseract-OCR"`.
The script copies the complete distribution, preserves its notices, executes
that copy, and fails if any required trained data is absent. It never downloads
anything.

## Production release flow

Install Inno Setup 6, prepare the vendored OCR runtime, then run:

```powershell
.\scripts\build_release.ps1
```

The build reads the one authoritative version from `pyproject.toml`, installs
the pinned Windows lock, cleans outputs, runs the 85% coverage quality gate,
builds through `packaging/pdf_to_excel.spec`, verifies the actual bundle and its
OCR languages, compiles the installer, creates the ZIP, and writes
`release\SHA256SUMS.txt`. `ISCC_PATH` can select a nonstandard compiler.

Official dependency lock updates must be generated on a clean Python 3.12 x64
Windows environment, followed by the complete quality gate, bundle self-test,
and clean-VM acceptance procedure before committing `requirements-windows.lock`.

### Optional identity and signing

- Place a properly licensed `assets/app.ico` to brand the EXE and installer.
- Set `APP_COMPANY`, `APP_PUBLISHER`, and `APP_COPYRIGHT` for metadata.
- Set `SIGNTOOL_PATH`, `WINDOWS_CERTIFICATE` (certificate-store thumbprint), and
  `TIMESTAMP_URL` to sign and verify the GUI executable and installer. Secrets
  and private keys must never be committed. Otherwise the build clearly warns
  that artifacts are unsigned.

### Optional onefile executable

Run `.\scripts\build_release.ps1 -Portable` or
`.\scripts\build_portable.ps1`. This creates
`release\PDF-to-Excel-Portable-{VERSION}-x64.exe`; it is not the production
default because it is larger, starts more slowly, extracts to a temporary
directory, and can attract more antivirus false positives.

## Packaged diagnostics

Both package forms support a non-GUI diagnostic:

```powershell
PDF-to-Excel.exe --self-test --output "C:\temp\pdf-to-excel-self-test.json"
```

It reports frozen/resource state, package version and imports, then executes the
bundled Tesseract and checks all required languages. It sends no telemetry or
document data.

## Clean Windows acceptance test

On a clean Windows 10/11 x64 VM with no Python, Tesseract, Visual Studio, or
checkout: copy only the installer; install and launch it from Start; convert a
digital and scanned PDF; test English, Serbian Cyrillic, Serbian Latin, and
mixed-script OCR; open the XLSX; save to normal user directories; repeat with
spaces, `č ć ž š đ`, and Cyrillic in paths; restart and launch again; then
uninstall through Installed Apps. Do not publish until every step passes.

## Limitations

Table reconstruction remains heuristic. Complex nested tables, handwriting,
damaged scans, and merged cells may require correction. Binary Windows artifacts
and clean-VM acceptance cannot be produced on non-Windows hosts. Third-party
components retain their own licenses; see `THIRD_PARTY_NOTICES.md`.

## License

MIT. Third-party components retain their own licenses.
