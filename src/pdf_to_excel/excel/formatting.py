from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet


def format_sheet(sheet: Worksheet) -> None:
    sheet.freeze_panes = "A2"
    sheet.sheet_view.showGridLines = True
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2F5597")
    for column in sheet.columns:
        letter = column[0].column_letter
        sheet.column_dimensions[letter].width = min(
            60, max(10, max(len(str(c.value or "")) for c in column) + 2)
        )
        for cell in column:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    sheet.auto_filter.ref = sheet.dimensions
