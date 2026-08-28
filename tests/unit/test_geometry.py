from pdf_to_excel.models import BoundingBox


def test_geometry_properties_and_overlap() -> None:
    box = BoundingBox(0, 0, 10, 20)
    assert (box.width, box.height, box.center_x, box.center_y) == (10, 20, 5, 10)
    other = BoundingBox(5, 10, 15, 30)
    assert box.intersection(other) == BoundingBox(5, 10, 10, 20)
    assert box.overlap_ratio(other) == 0.25
    assert box.contains(BoundingBox(1, 1, 2, 2))
