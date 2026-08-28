from enum import StrEnum

import cv2
import numpy as np


class OCRProfile(StrEnum):
    AUTO = "auto"
    CLEAN_SCAN = "clean_scan"
    LOW_CONTRAST = "low_contrast"
    PHOTO = "photo"


def to_grayscale(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()


def denoise(image: np.ndarray, strength: int = 7) -> np.ndarray:
    return cv2.fastNlMeansDenoising(to_grayscale(image), h=strength)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(to_grayscale(image))


def adaptive_binarize(image: np.ndarray) -> np.ndarray:
    return cv2.adaptiveThreshold(
        to_grayscale(image), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 35, 15,
    )


def preprocess(image: np.ndarray, profile: OCRProfile = OCRProfile.AUTO) -> np.ndarray:
    """Prepare an OCR image using an explicit, conservative profile."""
    gray = to_grayscale(image)
    if profile == OCRProfile.CLEAN_SCAN:
        return adaptive_binarize(gray)
    if profile == OCRProfile.LOW_CONTRAST:
        return adaptive_binarize(enhance_contrast(gray))
    if profile == OCRProfile.PHOTO:
        return adaptive_binarize(denoise(enhance_contrast(gray), 10))
    return adaptive_binarize(denoise(gray))


def remove_detected_table_lines(image: np.ndarray, horizontal_mask: np.ndarray,
                                vertical_mask: np.ndarray) -> np.ndarray:
    """Remove detected rules while retaining a clean, white OCR background."""
    gray = to_grayscale(image)
    mask = cv2.bitwise_or(horizontal_mask, vertical_mask)
    # A narrow inpaint radius avoids erasing glyph strokes touching a border.
    return cv2.inpaint(gray, mask, 1, cv2.INPAINT_TELEA)
