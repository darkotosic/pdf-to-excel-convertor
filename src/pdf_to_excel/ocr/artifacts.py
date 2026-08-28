from __future__ import annotations

import re


_RULE_ONLY = re.compile(r"^[\s|_—–.\-·]+$")


def is_ocr_table_artifact(
    text: str, *, field: str = "", confidence: float | None = None,
    touches_cell_border: bool = False,
) -> bool:
    """Identify residual table-rule glyphs without deleting valid identifiers."""
    value = text.strip()
    if not value:
        return False
    if _RULE_ONLY.fullmatch(value):
        return not (field in {"quantity", "inventory_number", "serial_number"}
                    and re.fullmatch(r"-\d+", value))
    # Tesseract commonly reads a short vertical rule as upper-case I.
    if value in {"|I", "I|", "||I", "I||"}:
        return touches_cell_border or confidence is None or confidence < 0.75
    rule_chars = sum(character in "|_—–.-·" for character in value)
    return (touches_cell_border and rule_chars / len(value) >= 0.7
            and (confidence is None or confidence < 0.6))
