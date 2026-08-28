from .base import TemplateMatch
from .revers import ReversTemplate


def detect_template(text: str, threshold: float = 0.55) -> TemplateMatch | None:
    match = ReversTemplate().detect(text)
    return match if match.confidence >= threshold else None
