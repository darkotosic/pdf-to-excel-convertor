import re
import unicodedata


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value.replace("\x00", ""))
    return re.sub(r"[ \t]+", " ", value).strip()
