from __future__ import annotations

from math import cos, radians, sin

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


def _regular_polygon(cx: float, cy: float, radius: float, sides: int, rotation_deg: float = 0) -> Polyline:
    points = [
        Point(cx + radius * cos(radians(rotation_deg + i * 360 / sides)), cy + radius * sin(radians(rotation_deg + i * 360 / sides)))
        for i in range(sides)
    ]
    return Polyline(points, closed=True)


def screenshot_1_variant_14() -> Drawing:
    """Variant 14 from the first screenshot: cone over hemisphere, circle with hexagon below."""
    entities: list = []
    cx = 100
    entities.extend(_center_mark(cx, 92, 105))
    entities.append(Polyline([Point(cx - 36, 112), Point(cx, 20), Point(cx + 36, 112)], closed=True))
    entities.append(Arc(Point(cx, 112), 40, 0, 180))
    entities.append(Line(Point(cx - 40, 112), Point(cx + 40, 112)))
    entities.append(Line(Point(cx, 20), Point(cx, 160), LineStyle.CENTER))
    entities.extend(_dimension(154, 20, 154, 130, "110", 160, 78))
    entities.append(Text(Point(122, 54), "α не", 6))

    entities.extend(_center_mark(cx, 240, 105))
    entities.append(Circle(Point(cx, 240), 40))
    entities.append(Circle(Point(cx, 240), 30))
    entities.append(_regular_polygon(cx, 240, 30, 6, 30))
    for angle in (30, 90, 150):
        dx = 30 * cos(radians(angle))
        dy = 30 * sin(radians(angle))
        entities.append(Line(Point(cx - dx, 240 - dy), Point(cx + dx, 240 + dy)))
    entities.extend(_dimension(58, 200, 58, 260, "⌀60", 37, 232))
    entities.append(Text(Point(132, 202), "⌀80", 6))
    return Drawing("variant_14_screenshot_1_horizontal", 200, 300, "horizontal", tuple(entities))


def screenshot_2_variant_14() -> Drawing:
    """Variant 14 from the second screenshot: prism/frustum above rectangle and circle under rectangle."""
    entities: list = []
    cx = 100
    entities.append(Polyline([Point(40, 86), Point(40, 162), Point(160, 162), Point(160, 86)], closed=True))
    entities.append(Polyline([Point(50, 50), Point(150, 50), Point(134, 86), Point(66, 86)], closed=True))
    entities.append(Polyline([Point(50, 50), Point(cx, 162), Point(150, 50)], closed=False, style=LineStyle.CONSTRUCTION))
    entities.extend(_center_mark(cx, 124, 130))
    entities.extend(_dimension(174, 50, 174, 150, "100", 180, 104))
    entities.extend(_dimension(74, 50, 74, 130, "80", 58, 92))

    entities.append(Polyline([Point(40, 215), Point(40, 295), Point(160, 295), Point(160, 215)], closed=True))
    entities.append(Circle(Point(cx, 295), 55))
    entities.extend(_center_mark(cx, 295, 135))
    entities.extend(_dimension(40, 200, 160, 200, "120", 90, 192))
    entities.extend(_dimension(168, 280, 168, 295, "15", 174, 290))
    entities.append(Text(Point(127, 350), "⌀110", 6))
    entities.append(Line(Point(126, 338), Point(152, 326), LineStyle.DIMENSION))
    return Drawing("variant_14_screenshot_2_horizontal", 210, 370, "horizontal", tuple(entities))


def screenshot_3_variant_14_vertical() -> Drawing:
    """Variant 14 from the third screenshot: vertical sheet with octagonal body and side boss."""
    entities: list = []
    cx, cy = 125, 150
    entities.append(_regular_polygon(cx, cy, 55, 8, 22.5))
    entities.append(Polyline([Point(42, 116), Point(80, 116), Point(80, 184), Point(42, 184)], closed=True))
    entities.append(Circle(Point(cx, cy), 45, LineStyle.CONSTRUCTION))
    entities.extend(_center_mark(cx, cy, 145))
    entities.extend(_dimension(82, 50, 142, 50, "60", 110, 42))
    entities.extend(_dimension(184, 90, 184, 210, "120", 190, 152))
    entities.extend(_dimension(96, 100, 96, 160, "⌀60", 76, 132))
    entities.extend(_dimension(146, 105, 146, 195, "⌀90", 152, 150))
    entities.extend(_dimension(80, 232, 170, 232, "⌀90", 114, 244))
    entities.append(Text(Point(108, 204), "R90", 6))
    entities.append(Text(Point(52, 200), "P", 6))
    return Drawing("variant_14_screenshot_3_vertical", 250, 300, "vertical", tuple(entities))


def all_drawings() -> dict[str, Drawing]:
    return {
        "Скриншот 1 — вариант 14 (горизонтально)": screenshot_1_variant_14(),
        "Скриншот 2 — вариант 14 (горизонтально)": screenshot_2_variant_14(),
        "Скриншот 3 — вариант 14 (вертикально)": screenshot_3_variant_14_vertical(),
    }
