from __future__ import annotations

from math import cos, radians, sin
from pathlib import Path
from xml.sax.saxutils import escape

from .model import Arc, Circle, Drawing, Line, LineStyle, Point, Polyline, Text

_STYLE = {
    LineStyle.SOLID: ("#111111", ""),
    LineStyle.CENTER: ("#777777", "8 5 2 5"),
    LineStyle.DIMENSION: ("#555555", "4 3"),
    LineStyle.CONSTRUCTION: ("#999999", "10 5"),
}


def _svg_style(style: LineStyle) -> str:
    color, dash = _STYLE[style]
    dash_part = f' stroke-dasharray="{dash}"' if dash else ""
    return f'stroke="{color}" stroke-width="1.4" fill="none"{dash_part}'


def _arc_path(arc: Arc) -> str:
    start = Point(
        arc.center.x + arc.radius * cos(radians(arc.start_angle)),
        arc.center.y + arc.radius * sin(radians(arc.start_angle)),
    )
    end = Point(
        arc.center.x + arc.radius * cos(radians(arc.end_angle)),
        arc.center.y + arc.radius * sin(radians(arc.end_angle)),
    )
    large = 1 if abs(arc.end_angle - arc.start_angle) > 180 else 0
    return f'M {start.x:.2f} {start.y:.2f} A {arc.radius:.2f} {arc.radius:.2f} 0 {large} 1 {end.x:.2f} {end.y:.2f}'


def drawing_to_svg(drawing: Drawing) -> str:
    min_x, min_y, max_x, max_y = drawing.bounds()
    pad = 20
    width = max(drawing.width, max_x - min_x) + pad * 2
    height = max(drawing.height, max_y - min_y) + pad * 2
    view_box = f"{min_x - pad:.2f} {min_y - pad:.2f} {width:.2f} {height:.2f}"
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" width="{width:.0f}mm" height="{height:.0f}mm">',
        '<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" fill="white" stroke="#dddddd"/>'.format(
            min_x - pad, min_y - pad, width, height
        ),
    ]
    for entity in drawing.entities:
        if isinstance(entity, Line):
            parts.append(
                f'<line x1="{entity.start.x:.2f}" y1="{entity.start.y:.2f}" x2="{entity.end.x:.2f}" y2="{entity.end.y:.2f}" {_svg_style(entity.style)}/>'
            )
        elif isinstance(entity, Circle):
            parts.append(f'<circle cx="{entity.center.x:.2f}" cy="{entity.center.y:.2f}" r="{entity.radius:.2f}" {_svg_style(entity.style)}/>')
        elif isinstance(entity, Arc):
            parts.append(f'<path d="{_arc_path(entity)}" {_svg_style(entity.style)}/>')
        elif isinstance(entity, Polyline):
            points = " ".join(f"{point.x:.2f},{point.y:.2f}" for point in entity.points)
            tag = "polygon" if entity.closed else "polyline"
            parts.append(f'<{tag} points="{points}" {_svg_style(entity.style)}/>')
        elif isinstance(entity, Text):
            color, _ = _STYLE[entity.style]
            parts.append(
                f'<text x="{entity.position.x:.2f}" y="{entity.position.y:.2f}" font-family="Arial, sans-serif" font-size="{entity.size:.2f}" fill="{color}">{escape(entity.value)}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def save_svg(drawing: Drawing, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(drawing_to_svg(drawing), encoding="utf-8")
    return output


def save_dxf(drawing: Drawing, path: str | Path) -> Path:
    """Save a simple AutoCAD-compatible DXF preview for systems without KOMPAS."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = ["0", "SECTION", "2", "ENTITIES"]

    def add_line(start: Point, end: Point) -> None:
        lines.extend(["0", "LINE", "8", "0", "10", str(start.x), "20", str(-start.y), "11", str(end.x), "21", str(-end.y)])

    for entity in drawing.entities:
        if isinstance(entity, Line):
            add_line(entity.start, entity.end)
        elif isinstance(entity, Circle):
            lines.extend(["0", "CIRCLE", "8", "0", "10", str(entity.center.x), "20", str(-entity.center.y), "40", str(entity.radius)])
        elif isinstance(entity, Arc):
            lines.extend([
                "0", "ARC", "8", "0", "10", str(entity.center.x), "20", str(-entity.center.y), "40", str(entity.radius),
                "50", str(-entity.end_angle), "51", str(-entity.start_angle),
            ])
        elif isinstance(entity, Polyline):
            pts = list(entity.points)
            for first, second in zip(pts, pts[1:]):
                add_line(first, second)
            if entity.closed and len(pts) > 1:
                add_line(pts[-1], pts[0])
        elif isinstance(entity, Text):
            lines.extend(["0", "TEXT", "8", "0", "10", str(entity.position.x), "20", str(-entity.position.y), "40", str(entity.size), "1", entity.value])
    lines.extend(["0", "ENDSEC", "0", "EOF"])
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def export_to_kompas(drawing: Drawing) -> None:
    """Create the drawing in KOMPAS-3D through its COM 2D API.

    The function intentionally uses late-bound classic 2D methods because they
    are available in many KOMPAS-3D releases. It should be called on Windows
    with KOMPAS-3D installed and pywin32 available.
    """
    try:
        import win32com.client
    except ImportError as exc:
        raise RuntimeError("Для экспорта в КОМПАС-3D установите pywin32 и запустите программу в Windows.") from exc

    try:
        kompas = win32com.client.Dispatch("KOMPAS.Application.5")
    except Exception as exc:  # noqa: BLE001 - COM raises many implementation-specific exceptions.
        raise RuntimeError("Не удалось подключиться к COM API КОМПАС-3D (KOMPAS.Application.5).") from exc

    kompas.Visible = True
    document = kompas.Document2D()
    document.ksCreateDocument("", 0)

    for entity in drawing.entities:
        if isinstance(entity, Line):
            document.ksLineSeg(entity.start.x, -entity.start.y, entity.end.x, -entity.end.y, 1)
        elif isinstance(entity, Circle):
            document.ksCircle(entity.center.x, -entity.center.y, entity.radius, 1)
        elif isinstance(entity, Arc):
            document.ksArcByAngle(entity.center.x, -entity.center.y, entity.radius, -entity.start_angle, -entity.end_angle, 1, 1)
        elif isinstance(entity, Polyline):
            pts = list(entity.points)
            for first, second in zip(pts, pts[1:]):
                document.ksLineSeg(first.x, -first.y, second.x, -second.y, 1)
            if entity.closed and len(pts) > 1:
                document.ksLineSeg(pts[-1].x, -pts[-1].y, pts[0].x, -pts[0].y, 1)
        elif isinstance(entity, Text):
            paragraph = document.ksParagraph(entity.position.x, -entity.position.y, 0, entity.size, 0)
            paragraph.ksTextLine(entity.value, 0)
            paragraph.ksEndObj()
