from PySide6.QtCore import QObject, Signal, Slot
from pdf_to_excel.conversion.pipeline import ConversionPipeline
from pdf_to_excel.models import ConversionOptions


class ConversionWorker(QObject):
    progress = Signal(int, str)
    succeeded = Signal(str)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, options: ConversionOptions) -> None:
        super().__init__()
        self.options = options
        self.cancelled = False

    @Slot()
    def run(self) -> None:
        try:
            result = ConversionPipeline().convert(
                self.options,
                lambda p: self.progress.emit(round(p.completed * 100 / p.total), p.message),
                lambda: self.cancelled,
            )
            self.succeeded.emit(str(result.output_path))
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.finished.emit()
