"""Deterministic test-document factories.

PDF fixtures are generated in pytest temporary directories so the repository does
not carry newly generated binary artifacts.
"""

from pathlib import Path

import fitz


def create_clean_scanned_ruled_pdf(destination: Path) -> Path:
    source = fitz.open()
    page = source.new_page(width=864, height=576)
    xs = (72, 360, 590, 792)
    ys = (90, 180, 270, 360, 450)
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]), color=(0, 0, 0), width=2)
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y), color=(0, 0, 0), width=2)
    # Rasterize the construction page and embed only that RGB image in the fixture.
    raster = page.get_pixmap(colorspace=fitz.csRGB, alpha=False, dpi=100)
    scanned = fitz.open()
    target = scanned.new_page(width=864, height=576)
    target.insert_image(target.rect, stream=raster.tobytes("png"))
    scanned.save(destination, garbage=4, deflate=True)
    scanned.close()
    source.close()
    return destination
