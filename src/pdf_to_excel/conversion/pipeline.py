from collections.abc import Callable
from time import monotonic

import fitz

from pdf_to_excel.config import Settings
from pdf_to_excel.exceptions import ConversionError
from pdf_to_excel.excel.exporter import export_tables
from pdf_to_excel.models import (ConversionOptions, ConversionResult, ConversionStatus,
                                 ConversionWarning, ExtractedTable, OutputMode, SourceType)
from pdf_to_excel.models import ExtractionSource
from pdf_to_excel.models import ReversDocument
from pdf_to_excel.pdf.digital_extractor import extract_digital_tables
from pdf_to_excel.tables.table_cleaner import clean_table
from pdf_to_excel.tables.cell_assignment import assign_words_to_cells
from .page_processor import PageProcessor
from .progress import ProgressCallback, ProgressUpdate


class ConversionPipeline:
    """Stream pages through PageProcessor and orchestrate one atomic export."""
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.load()

    def convert(self, options: ConversionOptions, progress: ProgressCallback | None = None,
                cancelled: Callable[[], bool] = lambda: False) -> ConversionResult:
        started = monotonic()
        if not options.input_path.is_file() or options.input_path.suffix.lower() != ".pdf":
            raise ConversionError("Izaberite postojeći PDF dokument.")
        try:
            document = fitz.open(options.input_path)
        except Exception as error:
            raise ConversionError("PDF dokument nije moguće otvoriti.") from error
        tables: list[ExtractedTable] = []
        structured: list[ReversDocument] = []
        warnings: list[ConversionWarning] = []
        source_counts = {source: 0 for source in ExtractionSource}
        processor = PageProcessor(options.input_path, self.settings, options.ocr_mode,
                                  options.dpi, options.languages)
        with document:
            pages = tuple(options.pages or range(1, document.page_count + 1))
            total_pages = len(pages)
            if any(page < 1 or page > document.page_count for page in pages):
                raise ConversionError("Izbor stranica je izvan opsega dokumenta.")
            for completed, page_number in enumerate(pages):
                if cancelled():
                    return ConversionResult(options.output_path, ConversionStatus.CANCELLED,
                                            tables, completed, list(structured), warnings)
                result = processor.process(document[page_number - 1])
                source_counts[result.extraction_source] += 1
                warnings.extend(result.warnings)
                if result.revers:
                    structured.append(result.revers)
                    if options.output_mode in (OutputMode.PRESERVE_TABLES, OutputMode.BOTH):
                        assert result.grid is not None
                        source = (SourceType.DIGITAL
                                  if result.extraction_source == ExtractionSource.NATIVE
                                  else SourceType.OCR)
                        tables.append(ExtractedTable(
                            page_number, 1, assign_words_to_cells(result.grid, result.words), source))
                elif options.output_mode != OutputMode.STRUCTURED:
                    extracted = result.tables or extract_digital_tables(
                        options.input_path, page_number)
                    cleaned = [clean_table(table) for table in extracted]
                    tables.extend(table for table in cleaned if table.rows)
                if progress:
                    progress(ProgressUpdate(completed + 1, len(pages),
                                            f"Obrađena stranica {page_number}"))
        if cancelled():
            return ConversionResult(options.output_path, ConversionStatus.CANCELLED,
                                    tables, len(pages), list(structured), warnings)
        final_path = export_tables(tables, options.output_path, structured,
                                   options.output_mode, options.include_empty_template_rows)
        status = (ConversionStatus.SUCCESS_WITH_WARNINGS if warnings
                  else ConversionStatus.SUCCESS)
        return ConversionResult(
            final_path,
            status,
            tables,
            len(pages),
            list(structured),
            warnings,
            total_pages=total_pages,
            native_pages=source_counts[ExtractionSource.NATIVE],
            ocr_pages=source_counts[ExtractionSource.OCR],
            mixed_pages=source_counts[ExtractionSource.HYBRID],
            tables_detected=len(tables),
            records_exported=sum(len(document.populated_items()) for document in structured),
            duration_seconds=monotonic() - started,
        )
