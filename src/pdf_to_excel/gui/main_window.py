import sys
from pathlib import Path
from PySide6.QtCore import QThread
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QWidget,
)
from pdf_to_excel.constants import APP_NAME
from pdf_to_excel.models import ConversionOptions
from pdf_to_excel.utils.files import default_output_path
from pdf_to_excel.utils.logging_config import configure_logging
from .conversion_worker import ConversionWorker
from .widgets import PdfDropEdit


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self._thread: QThread | None = None
        self._worker: ConversionWorker | None = None
        self.resize(720, 320)
        root, form = QWidget(), QFormLayout()
        self.input_edit, self.output_edit = PdfDropEdit(), PdfDropEdit()
        self.input_edit.pdf_dropped.connect(self._source_changed)
        form.addRow("PDF file", self._file_row(self.input_edit, self._choose_input))
        form.addRow("Excel file", self._file_row(self.output_edit, self._choose_output))
        self.languages = {
            code: QCheckBox(label)
            for code, label in (
                ("srp", "Serbian Cyrillic"),
                ("srp_latn", "Serbian Latin"),
                ("eng", "English"),
            )
        }
        language_row = QHBoxLayout()
        for checkbox in self.languages.values():
            checkbox.setChecked(True)
            language_row.addWidget(checkbox)
        form.addRow("OCR languages", language_row)
        form.addRow("OCR mode", QLabel("Automatic (per page)"))
        self.progress, self.convert_button = QProgressBar(), QPushButton("Convert to Excel")
        self.convert_button.clicked.connect(self._convert)
        form.addRow(self.progress)
        form.addRow(self.convert_button)
        root.setLayout(form)
        self.setCentralWidget(root)

    def _file_row(self, edit: PdfDropEdit, action):  # type: ignore[no-untyped-def]
        layout, button = QHBoxLayout(), QPushButton("Browse…")
        button.clicked.connect(action)
        layout.addWidget(edit)
        layout.addWidget(button)
        return layout

    def _choose_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF files (*.pdf)")
        if path:
            self.input_edit.setText(path)
            self._source_changed(path)

    def _source_changed(self, path: str) -> None:
        self.output_edit.setText(str(default_output_path(Path(path))))

    def _choose_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel", self.output_edit.text(), "Excel (*.xlsx)"
        )
        if path:
            self.output_edit.setText(path if path.lower().endswith(".xlsx") else path + ".xlsx")

    def _convert(self) -> None:
        languages = tuple(code for code, box in self.languages.items() if box.isChecked())
        if not languages:
            QMessageBox.warning(self, APP_NAME, "Select at least one OCR language.")
            return
        options = ConversionOptions(
            Path(self.input_edit.text()), Path(self.output_edit.text()), languages=languages
        )
        self._thread, self._worker = QThread(self), ConversionWorker(options)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._update_progress)
        self._worker.succeeded.connect(self._success)
        self._worker.failed.connect(lambda message: QMessageBox.critical(self, APP_NAME, message))
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(lambda: self.convert_button.setEnabled(True))
        self._thread.finished.connect(self._worker.deleteLater)
        self.convert_button.setEnabled(False)
        self._thread.start()

    def _update_progress(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self.statusBar().showMessage(message)

    def _success(self, path: str) -> None:
        if (
            QMessageBox.question(
                self, APP_NAME, f"Conversion complete.\n{path}\n\nOpen the workbook?"
            )
            == QMessageBox.StandardButton.Yes
        ):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))


def run() -> int:
    configure_logging()
    application = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return application.exec()
