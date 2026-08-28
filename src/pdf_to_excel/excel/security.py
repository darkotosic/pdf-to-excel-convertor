def safe_excel_text(value: str) -> str:
    """Prevent untrusted PDF text from becoming an Excel formula."""
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
