from __future__ import annotations

import cv2
import numpy as np


def estimate_skew_angle(image: np.ndarray, maximum_angle: float = 5.0) -> float:
    """Estimate small page skew from long horizontal rules."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    _, width = gray.shape[:2]
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 1800, threshold=max(50, width // 8),
        minLineLength=max(50, width // 4), maxLineGap=max(10, width // 100),
    )
    if lines is None:
        return 0.0
    angles: list[float] = []
    for x1, y1, x2, y2 in lines.reshape(-1, 4):
        angle = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        if abs(angle) <= maximum_angle:
            angles.append(angle)
    return float(np.median(angles)) if angles else 0.0


def deskew(image: np.ndarray, maximum_angle: float = 5.0) -> np.ndarray:
    """Correct a small skew without resampling an already straight page."""
    angle = estimate_skew_angle(image, maximum_angle)
    if abs(angle) < 0.1:
        return image
    height, width = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    return cv2.warpAffine(
        image, matrix, (width, height), flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255),
    )
