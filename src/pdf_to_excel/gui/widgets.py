from pathlib import Path
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLineEdit


class PdfDropEdit(QLineEdit):
    pdf_dropped = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):  # type: ignore[no-untyped-def]
        urls = event.mimeData().urls()
        if len(urls) == 1 and Path(urls[0].toLocalFile()).suffix.lower() == ".pdf":
            event.acceptProposedAction()

    def dropEvent(self, event):  # type: ignore[no-untyped-def]
        path = event.mimeData().urls()[0].toLocalFile()
        self.setText(path)
        self.pdf_dropped.emit(path)
