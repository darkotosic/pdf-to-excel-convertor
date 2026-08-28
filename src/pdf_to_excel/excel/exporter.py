from pathlib import Path
import os
import tempfile
from openpyxl import Workbook, load_workbook
from pdf_to_excel.models import ExtractedTable
from pdf_to_excel.text.type_inference import infer_value
from .formatting import format_sheet
from .security import safe_excel_text


def export_tables(tables: list[ExtractedTable], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination = available_output_path(destination)
    descriptor, name = tempfile.mkstemp(prefix=f".{destination.stem}-", suffix=".xlsx", dir=destination.parent)
    os.close(descriptor)
    temporary = Path(name)
    workbook = Workbook()
    active = workbook.active
    if active is not None:
        workbook.remove(active)
    if not tables:
        workbook.create_sheet("No tables found").append(["No tabular content was detected."])
    for table in tables:
        sheet = workbook.create_sheet(
            _unique_title(
                workbook.sheetnames, f"Page {table.page_number} Table {table.table_index}"
            )
        )
        for row in table.rows:
            values = []
            for cell in row:
                protected = safe_excel_text(cell.text)
                values.append(protected if protected != cell.text else infer_value(cell.text))
            sheet.append(values)
        format_sheet(sheet)
    try:
        workbook.save(temporary)
        verified = load_workbook(temporary, read_only=True)
        try:
            if not verified.sheetnames:
                raise ValueError("Generated workbook contains no sheets")
        finally:
            verified.close()
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def available_output_path(destination: Path) -> Path:
    if not destination.exists():
        return destination
    index = 1
    while True:
        candidate = destination.with_name(f"{destination.stem} ({index}){destination.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def _unique_title(existing: list[str], preferred: str) -> str:
    base = preferred[:31]
    title, index = base, 2
    while title in existing:
        suffix = f" ({index})"
        title, index = base[: 31 - len(suffix)] + suffix, index + 1
    return title
