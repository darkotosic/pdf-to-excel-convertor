from __future__ import annotations

import re
import unicodedata

from .base import TemplateMatch


def normalize_revers_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", text).casefold()
    value = re.sub(r"inventar\s*ski", "inventarski", value)
    value = re.sub(r"red\s*\.\s*broj", "red. broj", value)
    return re.sub(r"[^\wčćšđžљњђћџј.]+", " ", value).strip()


class ReversTemplate:
    name = "REVERS"
    anchors = (
        "revers", "dole navedena oprema", "red. broj", "vrsta računarske opreme",
        "model", "kol", "serijski broj", "inventarski broj",
        "zaključno sa rednim brojem", "datum predaje opreme",
        "opremu predao", "opremu primio",
    )

    def detect(self, text: str) -> TemplateMatch:
        normalized = normalize_revers_text(text)
        matched = tuple(anchor for anchor in self.anchors if anchor in normalized)
        # Title plus table vocabulary are independent high-value signals.
        score = len(matched) / len(self.anchors)
        if "revers" in matched:
            score += 0.12
        table_hits = sum(anchor in matched for anchor in self.anchors[2:8])
        if table_hits >= 4:
            score += 0.18
        return TemplateMatch(self.name, min(1.0, score), matched)
