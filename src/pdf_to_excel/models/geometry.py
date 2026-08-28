from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoundingBox:
    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        if self.x1 < self.x0 or self.y1 < self.y0:
            raise ValueError("Bounding box coordinates are inverted")

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def center_y(self) -> float:
        return (self.y0 + self.y1) / 2

    def intersection(self, other: BoundingBox) -> BoundingBox | None:
        x0, y0 = max(self.x0, other.x0), max(self.y0, other.y0)
        x1, y1 = min(self.x1, other.x1), min(self.y1, other.y1)
        return BoundingBox(x0, y0, x1, y1) if x1 >= x0 and y1 >= y0 else None

    def contains(self, other: BoundingBox) -> bool:
        return (
            self.x0 <= other.x0
            and self.y0 <= other.y0
            and self.x1 >= other.x1
            and self.y1 >= other.y1
        )

    def overlap_ratio(self, other: BoundingBox) -> float:
        intersection = self.intersection(other)
        if intersection is None or min(self.width * self.height, other.width * other.height) == 0:
            return 0.0
        return (
            intersection.width
            * intersection.height
            / min(self.width * self.height, other.width * other.height)
        )
