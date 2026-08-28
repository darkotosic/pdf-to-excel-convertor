from dataclasses import dataclass
from .geometry import BoundingBox


@dataclass(frozen=True, slots=True)
class OCRWord:
    text: str
    confidence: float
    bbox: BoundingBox
    page_number: int
