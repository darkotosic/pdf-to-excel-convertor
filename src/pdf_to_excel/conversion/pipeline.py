from collections.abc import Callable
import fitz
from pdf_to_excel.config import Settings
from pdf_to_excel.exceptions import CancelledError, ConversionError
from pdf_to_excel.models import ConversionOptions, ConversionResult, ExtractedTable, OCRMode
from pdf_to_excel.pdf.analyzer import analyze_page
from pdf_to_excel.pdf.digital_extractor import extract_digital_tables
from pdf_to_excel.pdf.renderer import render_page
from pdf_to_excel.ocr.preprocessing import preprocess
from pdf_to_excel.ocr.orientation import correct_orientation
from pdf_to_excel.ocr.tesseract_engine import TesseractEngine
from pdf_to_excel.tables.table_cleaner import clean_table
from pdf_to_excel.tables.table_reconstructor import reconstruct
from pdf_to_excel.excel.exporter import export_tables
from .progress import ProgressCallback, ProgressUpdate


class ConversionPipeline:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.load()

    def convert(
        self,
        options: ConversionOptions,
        progress: ProgressCallback | None = None,
        cancelled: Callable[[], bool] = lambda: False,
    ) -> ConversionResult:
        if not options.input_path.is_file() or options.input_path.suffix.lower() != ".pdf":
            raise ConversionError("Select an existing PDF file.")
        try:
            document = fitz.open(options.input_path)
        except Exception as error:
            raise ConversionError(f"Cannot open PDF: {error}") from error
        with document:
            pages = list(options.pages or range(1, document.page_count + 1))
            if any(page < 1 or page > document.page_count for page in pages):
                raise ConversionError("Page selection is outside the document range.")
            tables: list[ExtractedTable] = []
            engine = None
            for completed, page_number in enumerate(pages):
                if cancelled():
                    raise CancelledError("Conversion cancelled.")
                page = document[page_number - 1]
                analysis = analyze_page(page)
                use_ocr = options.ocr_mode == OCRMode.ALWAYS or (
                    options.ocr_mode == OCRMode.AUTOMATIC and not analysis.is_digital
                )
                if use_ocr:
                    engine = engine or TesseractEngine(
                        self.settings.tesseract_cmd, self.settings.confidence_threshold
                    )
                    words = engine.extract_words(
                        preprocess(correct_orientation(render_page(page, options.dpi))),
                        page_number,
                        options.languages,
                    )
                    page_tables = reconstruct(words, page_number)
                else:
                    page_tables = extract_digital_tables(options.input_path, page_number)
                tables.extend(clean_table(table) for table in page_tables)
                if progress:
                    progress(
                        ProgressUpdate(completed + 1, len(pages), f"Processed page {page_number}")
                    )
        export_tables(tables, options.output_path)
        return ConversionResult(options.output_path, tables, len(pages))
