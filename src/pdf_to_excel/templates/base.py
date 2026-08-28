from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TemplateMatch:
    name: str
    confidence: float
    matched_anchors: tuple[str, ...]


class DocumentTemplate(Protocol):
    name: str

    def detect(self, text: str) -> TemplateMatch: ...
