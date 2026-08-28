from __future__ import annotations

import cv2
import numpy as np

from pdf_to_excel.models import BoundingBox


def pdf_bbox_to_pixels(
    bbox: BoundingBox, page_width: float, page_height: float,
    image_width: int, image_height: int,
) -> BoundingBox:
    return BoundingBox(
        bbox.x0 * image_width / page_width, bbox.y0 * image_height / page_height,
        bbox.x1 * image_width / page_width, bbox.y1 * image_height / page_height,
    )


def has_visible_foreground(
    image: np.ndarray, bbox: BoundingBox, minimum_ratio: float = 0.015
) -> bool:
    """Return whether a rendered candidate region contains plausible glyph ink."""
    height, width = image.shape[:2]
    x0, y0 = max(0, int(bbox.x0)), max(0, int(bbox.y0))
    x1, y1 = min(width, int(np.ceil(bbox.x1))), min(height, int(np.ceil(bbox.y1)))
    if x1 <= x0 or y1 <= y0:
        return False
    region = image[y0:y1, x0:x1]
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY) if region.ndim == 3 else region
    threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    # Remove one-pixel cell borders before measuring glyph-like connected components.
    components, labels, stats, _ = cv2.connectedComponentsWithStats(threshold, connectivity=8)
    foreground = 0
    for index in range(1, components):
        component_width, component_height, area = (
            stats[index, cv2.CC_STAT_WIDTH], stats[index, cv2.CC_STAT_HEIGHT],
            stats[index, cv2.CC_STAT_AREA],
        )
        if area >= 2 and component_width < region.shape[1] * 0.9 and component_height < region.shape[0] * 0.9:
            foreground += int(area)
    return bool(foreground / max(1, region.size) >= minimum_ratio)
