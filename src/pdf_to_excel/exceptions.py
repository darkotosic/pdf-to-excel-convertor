class ConversionError(RuntimeError):
    """A user-facing conversion failure."""


class DependencyError(ConversionError):
    """A required local dependency is unavailable."""


class CancelledError(ConversionError):
    """The user cancelled conversion."""


class TesseractNotFoundError(DependencyError):
    """The configured or bundled Tesseract executable cannot be found."""


class MissingOcrLanguageError(DependencyError):
    """One or more requested Tesseract trained-data files are unavailable."""


class InvalidPdfError(ConversionError):
    """The selected file is not a readable PDF."""


class PasswordProtectedPdfError(InvalidPdfError):
    """The PDF requires a password."""


class DamagedPdfError(InvalidPdfError):
    """The PDF structure is damaged."""


class PdfRenderError(ConversionError):
    """A page could not be rendered into meaningful pixels."""


class PdfPageProcessingError(ConversionError):
    """A page could not be processed."""


class OcrTimeoutError(ConversionError):
    """An OCR operation exceeded its configured deadline."""


class ResourceLimitError(ConversionError):
    """A document exceeds a configured resource limit."""


class OutputPermissionError(ConversionError):
    """The output directory is not writable."""


class OutputFileLockedError(ConversionError):
    """The output workbook is locked by another application."""


class ExcelExportError(ConversionError):
    """The workbook could not be generated or verified."""
