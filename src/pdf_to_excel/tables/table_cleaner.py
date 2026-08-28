from pdf_to_excel.models import ExtractedTable
from pdf_to_excel.text.normalizer import normalize_text


def clean_table(table: ExtractedTable) -> ExtractedTable:
    for row in table.rows:
        for cell in row:
            cell.text = normalize_text(cell.text)
    table.rows = [row for row in table.rows if any(cell.text for cell in row)]
    return table
