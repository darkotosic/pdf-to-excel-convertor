from pdf_to_excel.excel.security import safe_excel_text
from pdf_to_excel.text.normalizer import normalize_text
from pdf_to_excel.text.type_inference import infer_value


def test_unicode_is_preserved_and_normalized() -> None:
    assert normalize_text("  Марко   Jovanović  ") == "Марко Jovanović"


def test_types_and_formula_security() -> None:
    assert infer_value("12") == 12
    assert infer_value("0641234567") == "0641234567"
    assert safe_excel_text("=cmd()") == "'=cmd()"
