from pathlib import Path
from openpyxl import Workbook
from pdf_to_excel.models import ExtractedTable
from pdf_to_excel.text.type_inference import infer_value
from .formatting import format_sheet
from .security import safe_excel_text


def export_tables(tables: list[ExtractedTable], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    workbook = Workbook()
    workbook.remove(workbook.active)
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
    workbook.save(temporary)
    temporary.replace(destination)


def _unique_title(existing: list[str], preferred: str) -> str:
    base = preferred[:31]
    title, index = base, 2
    while title in existing:
        suffix = f" ({index})"
        title, index = base[: 31 - len(suffix)] + suffix, index + 1
    return title
