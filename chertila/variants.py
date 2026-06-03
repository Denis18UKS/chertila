from __future__ import annotations

from .model import Arc, Circle, Drawing, Line, LineStyle, Point, Polyline, Text


def _center_mark(cx: float, cy: float, size: float = 70) -> tuple[Line, Line]:
    return (
        Line(Point(cx - size / 2, cy), Point(cx + size / 2, cy), LineStyle.CENTER),
        Line(Point(cx, cy - size / 2), Point(cx, cy + size / 2), LineStyle.CENTER),
    )


def _dimension(x1: float, y1: float, x2: float, y2: float, label: str, tx: float, ty: float) -> tuple[Line, Text]:
    return (
        Line(Point(x1, y1), Point(x2, y2), LineStyle.DIMENSION),
        Text(Point(tx, ty), label, 6),
    )


def screenshot_1_variant_14() -> Drawing:
    """Variant 14 from the first screenshot: cone over hemisphere and two concentric circles below."""
    entities: list = []
    cx = 100

    entities.extend(_center_mark(cx, 106, 118))
    entities.append(Polyline([Point(cx - 36, 125), Point(cx, 20), Point(cx + 36, 125)], closed=True))
    entities.append(Arc(Point(cx, 125), 40, 0, 180))
    entities.append(Line(Point(cx - 40, 125), Point(cx + 40, 125)))
    entities.append(Line(Point(cx, 20), Point(cx, 170), LineStyle.CENTER))
    entities.extend(_dimension(160, 20, 160, 130, "110", 166, 78))
    entities.append(Text(Point(124, 58), "α не", 6))

    entities.extend(_center_mark(cx, 245, 110))
    entities.append(Circle(Point(cx, 245), 40))
    entities.append(Circle(Point(cx, 245), 30))
    entities.extend(_dimension(58, 215, 58, 275, "⌀60", 38, 248))
    entities.append(Line(Point(123, 217), Point(151, 205), LineStyle.DIMENSION))
    entities.append(Text(Point(134, 204), "⌀80", 6))
    return Drawing("variant_14_screenshot_1_horizontal", 200, 310, "horizontal", tuple(entities))


def screenshot_2_variant_14() -> Drawing:
    """Variant 14 from the second screenshot: frustum over rectangle and circle under rectangle."""
    entities: list = []
    cx = 100

    entities.append(Polyline([Point(35, 82), Point(35, 162), Point(165, 162), Point(165, 82)], closed=True))
    entities.append(Polyline([Point(48, 42), Point(152, 42), Point(134, 82), Point(66, 82)], closed=True))
    entities.append(Polyline([Point(48, 42), Point(cx, 162), Point(152, 42)], closed=False, style=LineStyle.CONSTRUCTION))
    entities.extend(_center_mark(cx, 122, 135))
    entities.extend(_dimension(178, 42, 178, 142, "100", 184, 96))
    entities.extend(_dimension(74, 42, 74, 122, "80", 58, 86))

    entities.append(Polyline([Point(40, 220), Point(40, 300), Point(160, 300), Point(160, 220)], closed=True))
    entities.append(Circle(Point(cx, 300), 55))
    entities.extend(_center_mark(cx, 300, 140))
    entities.extend(_dimension(40, 205, 160, 205, "120", 90, 197))
    entities.extend(_dimension(172, 285, 172, 300, "15", 178, 295))
    entities.append(Line(Point(126, 338), Point(154, 352), LineStyle.DIMENSION))
    entities.append(Text(Point(126, 362), "⌀110", 6))
    return Drawing("variant_14_screenshot_2_horizontal", 210, 380, "horizontal", tuple(entities))


def screenshot_3_variant_14_vertical() -> Drawing:
    """Variant 14 from the third screenshot: vertical view with faceted body and left cylindrical boss."""
    entities: list = []
    cx, cy = 125, 150

    entities.append(
        Polyline(
            [
                Point(82, 110),
                Point(110, 70),
                Point(170, 70),
                Point(205, 96),
                Point(205, 204),
                Point(180, 230),
                Point(110, 230),
                Point(82, 190),
            ],
            closed=True,
        )
    )
    entities.append(Polyline([Point(42, 120), Point(82, 120), Point(82, 180), Point(42, 180)], closed=True))
    entities.append(Circle(Point(cx, cy), 45, LineStyle.CONSTRUCTION))
    entities.extend(_center_mark(cx, cy, 155))
    entities.extend(_dimension(110, 48, 170, 48, "60", 137, 40))
    entities.extend(_dimension(214, 90, 214, 210, "120", 220, 154))
    entities.extend(_dimension(96, 120, 96, 180, "⌀60", 70, 153))
    entities.extend(_dimension(150, 105, 150, 195, "⌀90", 156, 150))
    entities.extend(_dimension(90, 248, 180, 248, "⌀90", 122, 260))
    entities.append(Line(Point(105, 205), Point(130, 178), LineStyle.DIMENSION))
    entities.append(Text(Point(112, 204), "R90", 6))
    entities.append(Line(Point(52, 206), Point(72, 184), LineStyle.DIMENSION))
    entities.append(Text(Point(48, 220), "P", 6))
    return Drawing("variant_14_screenshot_3_vertical", 260, 310, "vertical", tuple(entities))


def all_drawings() -> dict[str, Drawing]:
    return {
        "Скриншот 1 — вариант 14 (горизонтально)": screenshot_1_variant_14(),
        "Скриншот 2 — вариант 14 (горизонтально)": screenshot_2_variant_14(),
        "Скриншот 3 — вариант 14 (вертикально)": screenshot_3_variant_14_vertical(),
    }
