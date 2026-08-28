import re
import cv2
import numpy as np
import pytesseract


def correct_orientation(image: np.ndarray) -> np.ndarray:
    try:
        rotation = int(re.search(r"Rotate: (\d+)", pytesseract.image_to_osd(image)).group(1))  # type: ignore[union-attr]
    except (pytesseract.TesseractError, AttributeError, ValueError):
        return image
    if rotation == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    if rotation == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    if rotation == 270:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image
