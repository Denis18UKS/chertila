from pathlib import Path

from chertila.exporters import drawing_to_svg, save_dxf, save_svg
from chertila.variants import all_drawings


def test_all_variant_14_drawings_are_available() -> None:
    drawings = all_drawings()
    assert len(drawings) == 3
    assert any(drawing.orientation == "vertical" for drawing in drawings.values())
    assert sum(drawing.orientation == "horizontal" for drawing in drawings.values()) == 2


def test_svg_contains_geometry_and_dimension_text(tmp_path: Path) -> None:
    drawing = next(iter(all_drawings().values()))
    svg = drawing_to_svg(drawing)
    assert "<svg" in svg
    assert "⌀80" in svg
    path = save_svg(drawing, tmp_path / "drawing.svg")
    assert path.read_text(encoding="utf-8").startswith("<?xml")


def test_dxf_contains_basic_entities(tmp_path: Path) -> None:
    drawing = all_drawings()["Скриншот 2 — вариант 14 (горизонтально)"]
    path = save_dxf(drawing, tmp_path / "drawing.dxf")
    content = path.read_text(encoding="utf-8")
    assert "SECTION" in content
    assert "CIRCLE" in content
    assert "LINE" in content
