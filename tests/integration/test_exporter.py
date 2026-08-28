from openpyxl import load_workbook
from pdf_to_excel.excel.exporter import export_tables
from pdf_to_excel.models import ExtractedTable, SourceType, TableCell


def test_exports_real_workbook(tmp_path) -> None:
    table = ExtractedTable(
        1,
        1,
        [
            [TableCell(0, 0, "БМ"), TableCell(0, 1, "Име")],
            [TableCell(1, 0, "12"), TableCell(1, 1, "Марко")],
        ],
        SourceType.DIGITAL,
    )
    output = tmp_path / "result.xlsx"
    export_tables([table], output)
    sheet = load_workbook(output).active
    assert sheet["A2"].value == 12
    assert sheet["B2"].value == "Марко"
