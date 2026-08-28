from pathlib import Path

from pdf_to_excel.models import ConversionResult, ConversionStatus


def test_conversion_result_has_explicit_success_status() -> None:
    result = ConversionResult(Path("result.xlsx"))
    assert result.status is ConversionStatus.SUCCESS
