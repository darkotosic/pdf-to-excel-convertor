# Third-party notices

Release bundles include unmodified third-party runtime components. They remain
the property of their respective copyright holders; the project's MIT license
does not replace their licenses.

- **Tesseract OCR** — Apache License 2.0. The prepared bundle must retain the
  upstream `LICENSE` and notices copied from the trusted distribution.
- **Leptonica and runtime libraries** — licenses and notices supplied by the
  selected trusted Tesseract distribution must remain in `vendor/tesseract`.
- **Qt for Python (PySide6)** — LGPLv3/GPLv3/commercial terms; see the Qt for
  Python distribution notices.
- **PyMuPDF, OpenCV, Pillow, NumPy, pdfplumber/pdfminer.six, pytesseract,
  openpyxl, pydantic, and platformdirs** — retain the license metadata and
  notices packaged by their distributions.

Before publishing a release, the release operator must audit the exact locked
versions and preserve all notices shipped in their wheels and in the selected
Tesseract distribution.
