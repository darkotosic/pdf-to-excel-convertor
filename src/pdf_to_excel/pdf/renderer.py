from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import logging

import fitz
import numpy as np
from PIL import Image

from pdf_to_excel.models import ConversionWarning

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RenderMetrics:
    minimum: int
    maximum: int
    mean: float
    standard_deviation: float
    near_black_ratio: float
    near_white_ratio: float

    @classmethod
    def calculate(cls, image: np.ndarray) -> "RenderMetrics":
        gray = image.mean(axis=2) if image.ndim == 3 else image
        return cls(
            int(gray.min()),
            int(gray.max()),
            float(gray.mean()),
            float(gray.std()),
            float(np.mean(gray <= 8)),
            float(np.mean(gray >= 247)),
        )

    @property
    def suspicious(self) -> bool:
        return self.near_black_ratio > 0.98 or self.standard_deviation < 0.75


@dataclass(frozen=True, slots=True)
class SafeRenderResult:
    image: np.ndarray
    metrics: RenderMetrics
    warnings: tuple[ConversionWarning, ...] = ()
    fallback_used: bool = False


def render_page(page: fitz.Page, dpi: int = 300) -> np.ndarray:
    """Render safely while retaining the historical ndarray-only API."""
    return render_page_safe(page, dpi).image


def render_page_safe(page: fitz.Page, dpi: int = 300) -> SafeRenderResult:
    """Render RGB with a local embedded-image fallback for broken colour profiles."""
    primary: np.ndarray | None = None
    try:
        pixmap = page.get_pixmap(dpi=dpi, colorspace=fitz.csRGB, alpha=False)
        primary = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
            pixmap.height, pixmap.width, 3
        ).copy()
        metrics = RenderMetrics.calculate(primary)
        if not metrics.suspicious:
            return SafeRenderResult(primary, metrics)
    except Exception:  # MuPDF exposes render failures through several exception types.
        logger.exception("Primary render failed for page %s", page.number + 1)

    fallback = _render_dominant_embedded_image(page, dpi)
    if fallback is None:
        if primary is None:
            raise RuntimeError(f"Unable to render PDF page {page.number + 1}")
        assert primary is not None
        return SafeRenderResult(primary, metrics)
    fallback_metrics = RenderMetrics.calculate(fallback)
    # Some malformed ICCBased images are decoded with reversed luminance even
    # after their profile is discarded. Recover the document polarity without
    # inventing content: every channel is transformed deterministically.
    if fallback_metrics.near_black_ratio > 0.98:
        fallback = 255 - fallback
        fallback_metrics = RenderMetrics.calculate(fallback)
    if fallback_metrics.suspicious:
        if primary is None:
            raise RuntimeError(f"Unable to render PDF page {page.number + 1}")
        return SafeRenderResult(primary, metrics)
    logger.warning("Page %s used embedded-image render fallback", page.number + 1)
    warning = ConversionWarning(
        "Primary PDF raster was suspicious; embedded image fallback was used",
        page.number + 1,
        code="RENDER_FALLBACK_USED",
        source=None,
    )
    return SafeRenderResult(fallback, fallback_metrics, (warning,), True)


def _render_dominant_embedded_image(page: fitz.Page, dpi: int) -> np.ndarray | None:
    scale = dpi / 72.0
    width, height = max(1, round(page.rect.width * scale)), max(1, round(page.rect.height * scale))
    page_area = page.rect.width * page.rect.height
    candidates: list[tuple[float, int, fitz.Rect]] = []
    for image_info in page.get_images(full=True):
        xref = image_info[0]
        for rect in page.get_image_rects(xref):
            coverage = rect.width * rect.height / page_area if page_area else 0
            if coverage >= 0.5:
                candidates.append((coverage, xref, rect))
    if not candidates:
        return None
    _, xref, rect = max(candidates)
    try:
        payload = page.parent.extract_image(xref)["image"]
        with Image.open(BytesIO(payload)) as source:
            source.load()
            # Conversion intentionally ignores an invalid embedded ICC profile.
            rgb = source.convert("RGB")
            target_width = max(1, round(rect.width * scale))
            target_height = max(1, round(rect.height * scale))
            rgb = rgb.resize((target_width, target_height), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (width, height), "white")
            canvas.paste(rgb, (round((rect.x0 - page.rect.x0) * scale),
                               round((rect.y0 - page.rect.y0) * scale)))
            return np.asarray(canvas, dtype=np.uint8).copy()
    except (OSError, ValueError, KeyError):
        logger.exception("Could not reconstruct page %s from embedded image", page.number + 1)
        return None
