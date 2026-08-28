from __future__ import annotations

from dataclasses import dataclass
import re

from pdf_to_excel.models import DetectedGrid, DocumentWord, ReversDocument


_PLACEHOLDERS = ("prezime i ime", "naziv organizacione jedinice", "ime i prezime")


@dataclass(frozen=True, slots=True)
class ReversFieldDefinition:
    semantic_name: str
    labels: tuple[str, ...]


FIELDS = (
    ReversFieldDefinition("person_identifier", ("jmbg", "identifik", "lični broj", "licni broj")),
    ReversFieldDefinition(
        "organization_unit", ("organizacion", "odeljenje", "organizacione jedinice")
    ),
    ReversFieldDefinition("person_name", ("prezime i ime", "ime i prezime", "zaposlen")),
)


def extract_revers_metadata(
    document: ReversDocument,
    words: list[DocumentWord],
    equipment_grid: DetectedGrid,
) -> None:
    """Extract values from geometric rows above the equipment grid.

    REVERS revisions place captions either beside a value or underneath it. For
    underlined captions, the closest text immediately above the caption is the
    value. Parenthesized captions are never eligible values.
    """
    candidates = [word for word in words if word.bbox.y1 < equipment_grid.bbox.y0]
    lines = _cluster_lines(candidates)
    for field in FIELDS:
        for index, line in enumerate(lines):
            folded = " ".join(word.text for word in line).casefold()
            if not any(label in folded for label in field.labels):
                continue
            value = _inline_value(line, field.labels)
            if not value and index:
                previous = lines[index - 1]
                if _vertically_close(previous, line) and _horizontal_overlap(previous, line):
                    label_words = [
                        word
                        for word in line
                        if any(label in word.text.casefold() for label in field.labels)
                    ] or line
                    label_x0 = min(word.bbox.x0 for word in label_words)
                    label_x1 = max(word.bbox.x1 for word in label_words)
                    region_words = [
                        word for word in previous if label_x0 <= word.bbox.center_x <= label_x1
                    ]
                    value = " ".join(word.text for word in region_words).strip()
            value = _clean_value(value)
            if not value:
                continue
            if field.semantic_name == "person_identifier":
                value = re.sub(r"\D", "", value)
            setattr(document, field.semantic_name, value)
            break


def _cluster_lines(words: list[DocumentWord]) -> list[list[DocumentWord]]:
    lines: list[list[DocumentWord]] = []
    for word in sorted(words, key=lambda item: (item.bbox.center_y, item.bbox.x0)):
        line = next(
            (
                row
                for row in reversed(lines)
                if abs(row[0].bbox.center_y - word.bbox.center_y)
                <= max(3.0, word.bbox.height * 0.6)
            ),
            None,
        )
        if line is None:
            lines.append([word])
        else:
            line.append(word)
    return [sorted(line, key=lambda item: item.bbox.x0) for line in lines]


def _inline_value(line: list[DocumentWord], labels: tuple[str, ...]) -> str:
    text = " ".join(word.text for word in line)
    if ":" in text:
        left, value = text.split(":", 1)
        if any(label in left.casefold() for label in labels):
            return value.strip()
    return ""


def _clean_value(value: str) -> str:
    stripped = value.strip(" _:-")
    folded = stripped.casefold().strip("() ")
    if not stripped or any(placeholder == folded for placeholder in _PLACEHOLDERS):
        return ""
    return stripped


def _vertically_close(above: list[DocumentWord], label: list[DocumentWord]) -> bool:
    gap = min(word.bbox.y0 for word in label) - max(word.bbox.y1 for word in above)
    height = max(word.bbox.height for word in label)
    return -height * 0.25 <= gap <= height * 2.5


def _horizontal_overlap(first: list[DocumentWord], second: list[DocumentWord]) -> bool:
    first_box = (min(w.bbox.x0 for w in first), max(w.bbox.x1 for w in first))
    second_box = (min(w.bbox.x0 for w in second), max(w.bbox.x1 for w in second))
    return min(first_box[1], second_box[1]) > max(first_box[0], second_box[0])
