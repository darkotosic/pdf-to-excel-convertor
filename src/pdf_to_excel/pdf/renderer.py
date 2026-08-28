import fitz
import numpy as np


def render_page(page: fitz.Page, dpi: int = 300) -> np.ndarray:
    pixmap = page.get_pixmap(dpi=dpi, colorspace=fitz.csRGB, alpha=False)
    return np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, 3)
