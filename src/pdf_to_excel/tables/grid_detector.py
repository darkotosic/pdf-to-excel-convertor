from __future__ import annotations

from pdf_to_excel.models import BoundingBox, DetectedGrid, DetectedLine


def detect_grids(
    horizontal: list[DetectedLine], vertical: list[DetectedLine], tolerance: float = 5.0
) -> list[DetectedGrid]:
    """Construct rectangular grids from intersecting table rules."""
    if len(horizontal) < 2 or len(vertical) < 2:
        return []
    xs = _cluster([line.start_x for line in vertical], tolerance)
    ys = _cluster([line.start_y for line in horizontal], tolerance)
    grids: list[DetectedGrid] = []
    for x_group in _continuous_groups(xs, vertical, horizontal, True, tolerance):
        related_y = [
            y for y in ys
            if any(line.start_x <= x_group[0] + tolerance and line.end_x >= x_group[-1] - tolerance
                   and abs(line.start_y - y) <= tolerance for line in horizontal)
        ]
        if len(x_group) >= 2 and len(related_y) >= 2:
            grids.append(DetectedGrid(
                BoundingBox(x_group[0], related_y[0], x_group[-1], related_y[-1]),
                tuple(related_y), tuple(x_group)
            ))
    return sorted(grids, key=lambda grid: grid.bbox.width * grid.bbox.height, reverse=True)


def _cluster(values: list[float], tolerance: float) -> list[float]:
    groups: list[list[float]] = []
    for value in sorted(values):
        if groups and value - groups[-1][-1] <= tolerance:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [sum(group) / len(group) for group in groups]


def _continuous_groups(
    xs: list[float], vertical: list[DetectedLine], horizontal: list[DetectedLine],
    _vertical_axis: bool, tolerance: float,
) -> list[list[float]]:
    if not xs:
        return []
    # Separate independent side-by-side tables where horizontal rules do not bridge them.
    groups: list[list[float]] = [[xs[0]]]
    for x in xs[1:]:
        previous = groups[-1][-1]
        bridged = any(line.start_x <= previous + tolerance and line.end_x >= x - tolerance
                      for line in horizontal)
        if bridged:
            groups[-1].append(x)
        else:
            groups.append([x])
    return groups


def cell_boxes(grid: DetectedGrid) -> list[list[BoundingBox]]:
    return [
        [BoundingBox(x0, y0, x1, y1) for x0, x1 in zip(grid.column_boundaries, grid.column_boundaries[1:])]
        for y0, y1 in zip(grid.row_boundaries, grid.row_boundaries[1:])
    ]
