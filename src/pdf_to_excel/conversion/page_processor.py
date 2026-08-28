from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

import fitz
import numpy as np

from pdf_to_excel.config import Settings
from pdf_to_excel.models import (BoundingBox, DetectedGrid, DocumentWord, OCRMode,
                                 PageType, ReversDocument, ConversionWarning)
from pdf_to_excel.ocr.deskew import deskew
from pdf_to_excel.ocr.orientation import correct_orientation
from pdf_to_excel.ocr.preprocessing import (OCRProfile, preprocess,
                                            remove_detected_table_lines)
from pdf_to_excel.ocr.tesseract_engine import TesseractEngine
from pdf_to_excel.pdf.analyzer import PageAnalysis, analyze_page
from pdf_to_excel.pdf.native_extractor import extract_native_words, extract_vector_lines
from pdf_to_excel.pdf.renderer import render_page
from pdf_to_excel.pdf.visibility_validator import has_visible_foreground, pdf_bbox_to_pixels
from pdf_to_excel.tables.grid_detector import detect_grids
from pdf_to_excel.tables.line_detector import detect_ruled_lines, merge_collinear
from pdf_to_excel.templates import detect_template
from pdf_to_excel.templates.base import TemplateMatch
from pdf_to_excel.templates.revers_processor import extract_revers, select_revers_equipment_grid


@dataclass(slots=True)
class PageResult:
    analysis: PageAnalysis
    template: TemplateMatch | None
    words: list[DocumentWord]
    grid: DetectedGrid | None = None
    grid_confidence: float = 0.0
    revers: ReversDocument | None = None
    warnings: list[ConversionWarning] = field(default_factory=list)


class PageProcessor:
    def __init__(self, source: Path, settings: Settings, ocr_mode: OCRMode,
                 dpi: int, languages: tuple[str, ...]) -> None:
        self.source, self.settings, self.ocr_mode = source, settings, ocr_mode
        self.dpi, self.languages = dpi, languages
        self._ocr: TesseractEngine | None = None

    def process(self, page: fitz.Page) -> PageResult:
        analysis = analyze_page(page)
        native = extract_native_words(page)
        native_match = detect_template(" ".join(word.text for word in native))
        force_ocr = self.ocr_mode == OCRMode.ALWAYS
        use_native = self.ocr_mode != OCRMode.ALWAYS and analysis.page_type != PageType.SCANNED
        rendered: np.ndarray | None = None
        words = native if use_native else []

        # Native PDF points are the canonical DIGITAL coordinate system.
        horizontal, vertical = extract_vector_lines(page)
        grids = detect_grids(merge_collinear(horizontal), merge_collinear(vertical), tolerance=2)
        grid, grid_confidence = select_revers_equipment_grid(grids, page.rect.width, page.rect.height)

        needs_raster = force_ocr or analysis.page_type in (PageType.SCANNED, PageType.MIXED) or grid is None
        if needs_raster:
            rendered = render_page(page, self.dpi)
            # Configure pytesseract before orientation detection (which invokes OSD).
            self._ensure_ocr()
            # All raster geometry and OCR use this same corrected coordinate system.
            oriented = deskew(correct_orientation(rendered))
            rh, rv, horizontal_mask, vertical_mask = detect_ruled_lines(oriented)
            raster_grids = detect_grids(rh, rv)
            raster_grid, raster_confidence = select_revers_equipment_grid(
                raster_grids, oriented.shape[1], oriented.shape[0])
            if (force_ocr or not use_native) and raster_grid is not None:
                grid, grid_confidence = raster_grid, raster_confidence
            elif grid is None and raster_grid is not None:
                grid = _scale_grid(raster_grid, page.rect.width / rendered.shape[1],
                                   page.rect.height / rendered.shape[0])
                grid_confidence = raster_confidence

            if force_ocr or analysis.page_type == PageType.SCANNED:
                # Geometry comes from the ruled original; OCR sees a rule-free copy.
                ocr_image = remove_detected_table_lines(
                    oriented, horizontal_mask, vertical_mask)
                words = self._extract_ocr(
                    preprocess(ocr_image, OCRProfile.CLEAN_SCAN), page.number + 1)

        if analysis.page_type == PageType.MIXED and self.ocr_mode != OCRMode.NEVER and not force_ocr:
            assert rendered is not None
            ocr_words = self._extract_ocr(preprocess(rendered), page.number + 1)
            ocr_words = _scale_words(ocr_words, page.rect.width / rendered.shape[1],
                                     page.rect.height / rendered.shape[0])
            words, merge_warnings = merge_document_words(native, ocr_words, page.number + 1)
        else:
            merge_warnings = []

        template = native_match or detect_template(" ".join(word.text for word in words))
        result = PageResult(analysis, template, words, grid, grid_confidence)
        result.warnings.extend(merge_warnings)
        if template and template.name == "REVERS" and grid is not None:
            if rendered is None:
                rendered = render_page(page, self.dpi)
            if use_native and not force_ocr:
                words = _suppress_phantoms(words, grid, rendered, page.rect.width, page.rect.height,
                                           result.warnings)
                result.words = words
            result.revers = extract_revers(self.source, page.number + 1, grid, words,
                                           template.confidence * grid_confidence)
            result.revers.warnings[:0] = result.warnings
        return result

    def _extract_ocr(self, image: np.ndarray, page_number: int) -> list[DocumentWord]:
        return self._ensure_ocr().extract_words(image, page_number, self.languages, psm=6)

    def _ensure_ocr(self) -> TesseractEngine:
        self._ocr = self._ocr or TesseractEngine(self.settings.tesseract_cmd,
                                                  self.settings.confidence_threshold)
        return self._ocr


def _scale_grid(grid: DetectedGrid, sx: float, sy: float) -> DetectedGrid:
    return DetectedGrid(BoundingBox(grid.bbox.x0*sx, grid.bbox.y0*sy,
                                    grid.bbox.x1*sx, grid.bbox.y1*sy),
                        tuple(y*sy for y in grid.row_boundaries),
                        tuple(x*sx for x in grid.column_boundaries))


def _scale_words(words: list[DocumentWord], sx: float, sy: float) -> list[DocumentWord]:
    return [DocumentWord(word.text, BoundingBox(word.bbox.x0*sx, word.bbox.y0*sy,
                                                word.bbox.x1*sx, word.bbox.y1*sy),
                         word.confidence, word.page_number, word.source) for word in words]


def merge_document_words(native: list[DocumentWord], ocr: list[DocumentWord],
                         page_number: int = 1) -> tuple[list[DocumentWord], list[ConversionWarning]]:
    merged, warnings = list(native), []
    for candidate in ocr:
        overlaps = [word for word in merged if word.bbox.overlap_ratio(candidate.bbox) >= .6]
        if not overlaps:
            merged.append(candidate)
            continue
        best = max(overlaps, key=lambda word: SequenceMatcher(None, word.text.casefold(),
                                                               candidate.text.casefold()).ratio())
        similarity = SequenceMatcher(None, best.text.casefold(), candidate.text.casefold()).ratio()
        if similarity < .7:
            warnings.append(ConversionWarning(
                "Native/OCR disagreement", page_number, value=candidate.text,
                confidence=candidate.confidence, source=candidate.source))
            if candidate.confidence > best.confidence:
                merged.remove(best)
                merged.append(candidate)
    return merged, warnings


def _suppress_phantoms(words: list[DocumentWord], grid: DetectedGrid, image: np.ndarray,
                       page_width: float, page_height: float,
                       warnings: list[ConversionWarning]) -> list[DocumentWord]:
    result = []
    for word in words:
        suspicious = (len(word.text.strip()) == 1 and not word.text.isdigit() and
                      grid.bbox.y0 < word.bbox.center_y < grid.bbox.y1)
        pixel_bbox = pdf_bbox_to_pixels(word.bbox, page_width, page_height,
                                        image.shape[1], image.shape[0])
        if suspicious and not has_visible_foreground(image, pixel_bbox):
            warnings.append(ConversionWarning(
                "Phantom native text suppressed", word.page_number, value=word.text,
                confidence=word.confidence, source=word.source))
            continue
        result.append(word)
    return result
