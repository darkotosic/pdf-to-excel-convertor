class ConversionError(RuntimeError):
    """A user-facing conversion failure."""


class DependencyError(ConversionError):
    """A required local dependency is unavailable."""


class CancelledError(ConversionError):
    """The user cancelled conversion."""
