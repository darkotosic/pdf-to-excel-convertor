from __future__ import annotations

from datetime import datetime
import re

from pdf_to_excel.models import ConversionWarning, DetectedGrid, DocumentWord, ReversDocument


_DATE = re.compile(r"(?<!\d)(\d{1,2})\s*(?:[./-]|\|)\s*(\d{1,2})\s*(?:[./-]|\|)\s*(\d{4})(?!\d)")


def extract_revers_footer(
    document: ReversDocument,
    words: list[DocumentWord],
    equipment_grid: DetectedGrid,
) -> None:
    footer_words = sorted(
        (word for word in words if word.bbox.y0 > equipment_grid.bbox.y1),
        key=lambda word: (word.bbox.y0, word.bbox.x0),
    )
    text = " ".join(word.text for word in footer_words)
    date_match = _DATE.search(text)
    if date_match:
        raw = date_match.group(0)
        try:
            document.handover_date = datetime.strptime(
                ".".join(date_match.groups()), "%d.%m.%Y"
            ).date()
        except ValueError:
            document.warnings.append(
                ConversionWarning(
                    "Invalid handover date",
                    document.page_number,
                    field="handover_date",
                    value=raw,
                )
            )
    closing = re.search(
        r"zaključno\s+sa\s+rednim\s+brojem\s*[:._-]*\s*([\w.-]+)", text, flags=re.IGNORECASE
    )
    if closing:
        document.closing_item_number = closing.group(1)
    for line in _lines(footer_words):
        line_text = " ".join(word.text for word in line)
        if ":" not in line_text:
            continue
        label, value = (part.strip(" _") for part in line_text.split(":", 1))
        if not value:
            continue
        folded = label.casefold()
        if "opremu predao" in folded:
            document.handed_over_by = value
        elif "opremu primio" in folded:
            document.received_by = value


def _lines(words: list[DocumentWord]) -> list[list[DocumentWord]]:
    lines: list[list[DocumentWord]] = []
    for word in words:
        if not lines or abs(lines[-1][0].bbox.center_y - word.bbox.center_y) > max(
            3.0, word.bbox.height * 0.6
        ):
            lines.append([word])
        else:
            lines[-1].append(word)
    return lines
