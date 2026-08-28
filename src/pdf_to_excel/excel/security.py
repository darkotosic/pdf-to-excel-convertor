def safe_excel_text(value: str | int | float) -> str | int | float:
    """Prevent untrusted PDF text from becoming an Excel formula."""
    if not isinstance(value, str):
        return value
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
