from collections.abc import Callable

import fitz

from pdf_to_excel.config import Settings
from pdf_to_excel.exceptions import CancelledError, ConversionError
from pdf_to_excel.excel.exporter import export_tables
from pdf_to_excel.models import ConversionOptions, ConversionResult, ExtractedTable, OutputMode
from pdf_to_excel.pdf.digital_extractor import extract_digital_tables
from pdf_to_excel.tables.table_cleaner import clean_table
from .page_processor import PageProcessor
from .progress import ProgressCallback, ProgressUpdate


class ConversionPipeline:
    """Stream pages through PageProcessor and orchestrate one atomic export."""
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.load()

    def convert(self, options: ConversionOptions, progress: ProgressCallback | None = None,
                cancelled: Callable[[], bool] = lambda: False) -> ConversionResult:
        if not options.input_path.is_file() or options.input_path.suffix.lower() != ".pdf":
            raise ConversionError("Select an existing PDF file.")
        try:
            document = fitz.open(options.input_path)
        except Exception as error:
            raise ConversionError("The PDF could not be opened.") from error
        tables: list[ExtractedTable] = []
        structured = []
        processor = PageProcessor(options.input_path, self.settings, options.ocr_mode,
                                  options.dpi, options.languages)
        with document:
            pages = tuple(options.pages or range(1, document.page_count + 1))
            if any(page < 1 or page > document.page_count for page in pages):
                raise ConversionError("Page selection is outside the document range.")
            for completed, page_number in enumerate(pages):
                if cancelled():
                    raise CancelledError("Conversion cancelled.")
                result = processor.process(document[page_number - 1])
                if result.revers:
                    structured.append(result.revers)
                elif options.output_mode != OutputMode.STRUCTURED:
                    cleaned = [clean_table(table) for table in
                               extract_digital_tables(options.input_path, page_number)]
                    tables.extend(table for table in cleaned if table.rows)
                if progress:
                    progress(ProgressUpdate(completed + 1, len(pages),
                                            f"Processed page {page_number}"))
        if cancelled():
            raise CancelledError("Conversion cancelled.")
        final_path = export_tables(tables, options.output_path, structured,
                                   options.output_mode, options.include_empty_template_rows)
        return ConversionResult(final_path, tables, len(pages), list(structured))
