from pdf_to_excel.models import OCRWord


def cluster_rows(words: list[OCRWord]) -> list[list[OCRWord]]:
    rows: list[list[OCRWord]] = []
    for word in sorted(words, key=lambda w: (w.bbox.center_y, w.bbox.x0)):
        tolerance = max(5.0, word.bbox.height * 0.6)
        row = next(
            (r for r in rows if abs(r[0].bbox.center_y - word.bbox.center_y) <= tolerance), None
        )
        if row is None:
            rows.append([word])
        else:
            row.append(word)
    for row in rows:
        row.sort(key=lambda w: w.bbox.x0)
    return rows


def reconstruct_cell_text(words: list[OCRWord], preserve_line_breaks: bool = False) -> str:
    """Join cell words in visual order while preserving wrapped identifiers."""
    lines = cluster_rows(words)
    rendered = [" ".join(word.text.strip() for word in line if word.text.strip()) for line in lines]
    rendered = [line for line in rendered if line]
    if preserve_line_breaks:
        return "\n".join(rendered)
    result = ""
    for line in rendered:
        if not result:
            result = line
        elif result.endswith("-"):
            result += line
        else:
            result += " " + line
    return result
