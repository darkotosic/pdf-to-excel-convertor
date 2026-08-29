from __future__ import annotations

import fitz

from pdf_to_excel.models import BoundingBox, DetectedLine, DocumentWord, WordSource


def extract_native_words(page: fitz.Page) -> list[DocumentWord]:
    """Extract words in PyMuPDF's top-left page coordinate system (PDF points)."""
    return [
        DocumentWord(
            str(word[4]),
            BoundingBox(*map(float, word[:4])),
            1.0,
            page.number + 1,
            WordSource.NATIVE,
        )
        for word in page.get_text("words")
        if str(word[4]).strip()
    ]


def extract_vector_lines(page: fitz.Page) -> tuple[list[DetectedLine], list[DetectedLine]]:
    lines: list[DetectedLine] = []
    for drawing in page.get_drawings():
        width = float(drawing.get("width", 1.0) or 1.0)
        for item in drawing.get("items", ()):
            if item[0] == "l":
                p1, p2 = item[1], item[2]
                lines.append(DetectedLine(p1.x, p1.y, p2.x, p2.y, width))
            elif item[0] == "re":
                rect = item[1]
                lines.extend(
                    (
                        DetectedLine(rect.x0, rect.y0, rect.x1, rect.y0, width),
                        DetectedLine(rect.x0, rect.y1, rect.x1, rect.y1, width),
                        DetectedLine(rect.x0, rect.y0, rect.x0, rect.y1, width),
                        DetectedLine(rect.x1, rect.y0, rect.x1, rect.y1, width),
                    )
                )
    return (
        [line for line in lines if line.horizontal],
        [line for line in lines if not line.horizontal],
    )
