from __future__ import annotations

import cv2
import numpy as np

from pdf_to_excel.models import DetectedLine


def detect_ruled_lines(
    image: np.ndarray, minimum_length_ratio: float = 0.08
) -> tuple[list[DetectedLine], list[DetectedLine], np.ndarray, np.ndarray]:
    """Detect horizontal and vertical rules without interpreting them as OCR text."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 13
    )
    height, width = gray.shape[:2]
    horizontal_mask = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (max(10, width // 30), 1)),
    )
    vertical_mask = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(10, height // 30))),
    )
    horizontal = _mask_lines(horizontal_mask, True, width * minimum_length_ratio)
    vertical = _mask_lines(vertical_mask, False, height * minimum_length_ratio)
    return merge_collinear(horizontal), merge_collinear(vertical), horizontal_mask, vertical_mask


def _mask_lines(mask: np.ndarray, horizontal: bool, minimum: float) -> list[DetectedLine]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    result: list[DetectedLine] = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        length = width if horizontal else height
        if length < minimum:
            continue
        if horizontal:
            result.append(DetectedLine(x, y + height / 2, x + width, y + height / 2, height))
        else:
            result.append(DetectedLine(x + width / 2, y, x + width / 2, y + height, width))
    return result


def merge_collinear(
    lines: list[DetectedLine], tolerance: float = 3.0, gap: float = 12.0
) -> list[DetectedLine]:
    """Merge fragments on nearly identical axes and discard duplicates."""
    merged: list[DetectedLine] = []
    for line in sorted(lines, key=lambda item: (item.start_y, item.start_x)):
        for index, current in enumerate(merged):
            if line.horizontal != current.horizontal:
                continue
            if line.horizontal:
                same_axis = abs(line.start_y - current.start_y) <= tolerance
                touches = (
                    line.start_x <= current.end_x + gap and line.end_x >= current.start_x - gap
                )
                if same_axis and touches:
                    y = (line.start_y + current.start_y) / 2
                    merged[index] = DetectedLine(
                        min(line.start_x, current.start_x),
                        y,
                        max(line.end_x, current.end_x),
                        y,
                        max(line.thickness, current.thickness),
                    )
                    break
            else:
                same_axis = abs(line.start_x - current.start_x) <= tolerance
                touches = (
                    line.start_y <= current.end_y + gap and line.end_y >= current.start_y - gap
                )
                if same_axis and touches:
                    x = (line.start_x + current.start_x) / 2
                    merged[index] = DetectedLine(
                        x,
                        min(line.start_y, current.start_y),
                        x,
                        max(line.end_y, current.end_y),
                        max(line.thickness, current.thickness),
                    )
                    break
        else:
            merged.append(line)
    return merged
