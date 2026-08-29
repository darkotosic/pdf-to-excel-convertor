from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import logging

import fitz
import numpy as np
from PIL import Image
import cv2

from pdf_to_excel.exceptions import PdfRenderError
from pdf_to_excel.models import ConversionWarning, WarningCode, WarningSeverity

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RenderMetrics:
    minimum: int
    maximum: int
    mean: float
    standard_deviation: float
    near_black_ratio: float
    near_white_ratio: float
    foreground_pixel_ratio: float
    edge_density: float
    connected_component_count: int
    foreground_bbox_area_ratio: float

    @classmethod
    def calculate(cls, image: np.ndarray) -> "RenderMetrics":
        gray = image.mean(axis=2) if image.ndim == 3 else image
        gray_u8 = np.clip(gray, 0, 255).astype(np.uint8)
        foreground = gray_u8 < 240
        edges = cv2.Canny(gray_u8, 60, 180)
        count, _, stats, _ = cv2.connectedComponentsWithStats(
            foreground.astype(np.uint8), connectivity=8
        )
        meaningful = stats[1:, cv2.CC_STAT_AREA] >= 4 if count > 1 else np.array([], dtype=bool)
        points = cv2.findNonZero(foreground.astype(np.uint8))
        bbox_ratio = 0.0
        if points is not None:
            _, _, width, height = cv2.boundingRect(points)
            bbox_ratio = width * height / max(1, gray_u8.size)
        return cls(
            int(gray.min()),
            int(gray.max()),
            float(gray.mean()),
            float(gray.std()),
            float(np.mean(gray <= 8)),
            float(np.mean(gray >= 247)),
            float(np.mean(foreground)),
            float(np.mean(edges > 0)),
            int(np.count_nonzero(meaningful)),
            float(bbox_ratio),
        )

    @property
    def suspicious(self) -> bool:
        return RenderQuality.evaluate(self).is_suspicious


@dataclass(frozen=True, slots=True)
class RenderQuality:
    metrics: RenderMetrics
    is_suspicious: bool
    reasons: tuple[str, ...]

    @classmethod
    def evaluate(
        cls, metrics: RenderMetrics, *, expects_image: bool = False, icc_failure: bool = False
    ) -> "RenderQuality":
        reasons: list[str] = []
        if metrics.near_black_ratio > 0.98:
            reasons.append("NEAR_BLACK")
        if metrics.near_white_ratio > 0.99:
            reasons.append("NEAR_WHITE")
        if metrics.standard_deviation < 0.75:
            reasons.append("LOW_VARIANCE")
        if metrics.edge_density < 0.0001:
            reasons.append("NO_EDGES")
        if expects_image and (
            metrics.foreground_pixel_ratio < 0.005 or metrics.foreground_bbox_area_ratio < 0.05
        ):
            reasons.append("EMBEDDED_IMAGE_CONTENT_MISSING")
        if icc_failure:
            reasons.append("ICC_PROFILE_FAILURE")
        return cls(metrics, bool(reasons), tuple(reasons))


@dataclass(frozen=True, slots=True)
class SafeRenderResult:
    image: np.ndarray
    metrics: RenderMetrics
    warnings: tuple[ConversionWarning, ...] = ()
    fallback_used: bool = False
    quality: RenderQuality | None = None
    fallback_method: str | None = None


def render_page(page: fitz.Page, dpi: int = 300) -> np.ndarray:
    """Render safely while retaining the historical ndarray-only API."""
    return render_page_safe(page, dpi).image


def render_page_safe(page: fitz.Page, dpi: int = 300) -> SafeRenderResult:
    """Render RGB with a local embedded-image fallback for broken colour profiles."""
    primary: np.ndarray | None = None
    try:
        pixmap = page.get_pixmap(dpi=dpi, colorspace=fitz.csRGB, alpha=False)
        primary = (
            np.frombuffer(pixmap.samples, dtype=np.uint8)
            .reshape(pixmap.height, pixmap.width, 3)
            .copy()
        )
        metrics = RenderMetrics.calculate(primary)
        quality = RenderQuality.evaluate(metrics, expects_image=_has_dominant_image(page))
        if not quality.is_suspicious:
            return SafeRenderResult(primary, metrics, quality=quality)
    except Exception:  # MuPDF exposes render failures through several exception types.
        logger.exception("Primary render failed for page %s", page.number + 1)

    fallback, method = _render_embedded_image_fallbacks(page, dpi)
    if fallback is None:
        raise PdfRenderError(f"Unable to render meaningful content on PDF page {page.number + 1}")
    fallback_metrics = RenderMetrics.calculate(fallback)
    # Some malformed ICCBased images are decoded with reversed luminance even
    # after their profile is discarded. Recover the document polarity without
    # inventing content: every channel is transformed deterministically.
    if fallback_metrics.near_black_ratio > 0.98:
        inverted = 255 - fallback
        inverted_metrics = RenderMetrics.calculate(inverted)
        inverted_quality = RenderQuality.evaluate(inverted_metrics, expects_image=True)
        if (
            not inverted_quality.is_suspicious
            and inverted_metrics.edge_density > fallback_metrics.edge_density
        ):
            fallback, fallback_metrics = inverted, inverted_metrics
            method = f"{method}+validated-inversion"
    fallback_quality = RenderQuality.evaluate(fallback_metrics, expects_image=True)
    if fallback_quality.is_suspicious:
        raise PdfRenderError(
            f"PDF page {page.number + 1} fallback is suspicious: "
            + ", ".join(fallback_quality.reasons)
        )
    logger.warning("Page %s used embedded-image render fallback", page.number + 1)
    warning = ConversionWarning(
        "Primary PDF raster was suspicious; embedded image fallback was used",
        page.number + 1,
        code=WarningCode.RENDER_FALLBACK_USED,
        severity=WarningSeverity.WARNING,
        source=None,
    )
    return SafeRenderResult(fallback, fallback_metrics, (warning,), True, fallback_quality, method)


def _has_dominant_image(page: fitz.Page) -> bool:
    page_area = page.rect.width * page.rect.height
    return any(
        rect.width * rect.height >= page_area * 0.5
        for image in page.get_images(full=True)
        for rect in page.get_image_rects(image[0])
    )


def _render_embedded_image_fallbacks(
    page: fitz.Page, dpi: int
) -> tuple[np.ndarray | None, str | None]:
    for renderer, name in (
        (_render_image_pixmap, "pymupdf-xref-pixmap"),
        (_render_dominant_embedded_image, "pillow-icc-ignored"),
    ):
        image = renderer(page, dpi)
        if image is not None:
            quality = RenderQuality.evaluate(RenderMetrics.calculate(image), expects_image=True)
            if not quality.is_suspicious or quality.metrics.near_black_ratio > 0.98:
                return image, name
    return None, None


def _render_image_pixmap(page: fitz.Page, dpi: int) -> np.ndarray | None:
    candidate = _dominant_image(page)
    if candidate is None:
        return None
    xref, rect = candidate
    try:
        source = fitz.Pixmap(page.parent, xref)
        if source.alpha or source.n != 3:
            source = fitz.Pixmap(fitz.csRGB, source)
        image = (
            np.frombuffer(source.samples, np.uint8)
            .reshape(source.height, source.width, source.n)[:, :, :3]
            .copy()
        )
        return _place_image(image, page, rect, dpi)
    except Exception:
        logger.exception("Pixmap fallback failed for page %s", page.number + 1)
        return None


def _dominant_image(page: fitz.Page) -> tuple[int, fitz.Rect] | None:
    page_area = page.rect.width * page.rect.height
    candidates = [
        (rect.width * rect.height / page_area, image[0], rect)
        for image in page.get_images(full=True)
        for rect in page.get_image_rects(image[0])
        if page_area
    ]
    if not candidates:
        return None
    coverage, xref, rect = max(candidates)
    return (xref, rect) if coverage >= 0.5 else None


def _place_image(image: np.ndarray, page: fitz.Page, rect: fitz.Rect, dpi: int) -> np.ndarray:
    scale = dpi / 72
    canvas = Image.new(
        "RGB",
        (max(1, round(page.rect.width * scale)), max(1, round(page.rect.height * scale))),
        "white",
    )
    source = Image.fromarray(image).resize(
        (max(1, round(rect.width * scale)), max(1, round(rect.height * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas.paste(
        source, (round((rect.x0 - page.rect.x0) * scale), round((rect.y0 - page.rect.y0) * scale))
    )
    return np.asarray(canvas, dtype=np.uint8).copy()


def _render_dominant_embedded_image(page: fitz.Page, dpi: int) -> np.ndarray | None:
    scale = dpi / 72.0
    width, height = max(1, round(page.rect.width * scale)), max(1, round(page.rect.height * scale))
    candidate = _dominant_image(page)
    if candidate is None:
        return None
    xref, rect = candidate
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
            canvas.paste(
                rgb,
                (round((rect.x0 - page.rect.x0) * scale), round((rect.y0 - page.rect.y0) * scale)),
            )
            return np.asarray(canvas, dtype=np.uint8).copy()
    except (OSError, ValueError, KeyError):
        logger.exception("Could not reconstruct page %s from embedded image", page.number + 1)
        return None
