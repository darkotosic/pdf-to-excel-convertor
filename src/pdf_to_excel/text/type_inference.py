from datetime import datetime
from decimal import Decimal, InvalidOperation
import re


def infer_value(text: str) -> str | int | float | datetime:
    value = text.strip()
    if not value or (len(value) > 1 and value.startswith("0")):
        return value
    if re.fullmatch(r"[-+]?\d+", value):
        return int(value)
    if re.fullmatch(r"[-+]?\d+[.,]\d+", value):
        try:
            return float(Decimal(value.replace(",", ".")))
        except InvalidOperation:
            pass
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return value
