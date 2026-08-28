import cv2
import numpy as np


def preprocess(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 15
    )


def remove_detected_table_lines(image: np.ndarray, horizontal_mask: np.ndarray,
                                vertical_mask: np.ndarray) -> np.ndarray:
    """Remove detected rules while retaining a clean, white OCR background."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()
    mask = cv2.bitwise_or(horizontal_mask, vertical_mask)
    # A narrow inpaint radius avoids erasing glyph strokes touching a border.
    return cv2.inpaint(gray, mask, 1, cv2.INPAINT_TELEA)
