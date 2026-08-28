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
