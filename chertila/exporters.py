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


KO_DOCUMENT_PARAM = 35
LT_DOC_SHEET_STANDARD = 1


def _dispatch_kompas_api5(win32com_client):
    """Connect to KOMPAS API5 and prefer a typed KompasObject wrapper."""
    try:
        module5 = win32com_client.gencache.EnsureModule(
            "{0422828C-F174-495E-AC5D-D31014DBBE87}", 0, 1, 0
        )
        return win32com_client.Dispatch(
            "KOMPAS.Application.5", None, module5.KompasObject.CLSID
        )
    except Exception:
        return win32com_client.Dispatch("KOMPAS.Application.5")


def _set_com_property(obj, name: str, value) -> None:
    setter = getattr(obj, f"Set{name[:1].upper()}{name[1:]}", None)
    if callable(setter):
        setter(value)
        return
    setattr(obj, name, value)


def _create_document2d(kompas, win32com_client):
    """Create a visible 2D drawing and return the API5 ksDocument2D object."""
    try:
        document = kompas.Document2D()
    except Exception:
        return _create_document2d_with_api7(kompas, win32com_client)

    document_param = kompas.GetParamStruct(KO_DOCUMENT_PARAM)
    _set_com_property(document_param, "type", LT_DOC_SHEET_STANDARD)
    _set_com_property(document_param, "regime", 0)
    created = document.ksCreateDocument(document_param)
    if not created:
        raise RuntimeError("КОМПАС-3D вернул отказ при создании 2D-чертежа.")
    return document


def _create_document2d_with_api7(kompas, win32com_client):
    """Create a drawing through API7 when API5 Document2D is unavailable."""
    application7 = None
    try:
        application7 = kompas.ksGetApplication7()
    except Exception:
        try:
            application7 = win32com_client.Dispatch("KOMPAS.Application.7")
        except Exception as exc:
            raise RuntimeError(
                "Не удалось получить интерфейс Document2D API5 или создать чертёж через API7."
            ) from exc

    application7.Visible = True
    for args in ((LT_DOC_SHEET_STANDARD, True), (LT_DOC_SHEET_STANDARD,), (LT_DOC_SHEET_STANDARD, "", True)):
        try:
            application7.Documents.Add(*args)
            break
        except Exception:
            continue
    else:
        raise RuntimeError("Не удалось создать новый чертёж через KOMPAS API7 Documents.Add.")

    for api5 in (kompas, _dispatch_kompas_api5(win32com_client)):
        try:
            return api5.ActiveDocument2D()
        except Exception:
            continue
    raise RuntimeError("Чертёж создан, но API5 ActiveDocument2D недоступен.")


def _draw_to_kompas_document(document, drawing: Drawing) -> None:
    for entity in drawing.entities:
        if isinstance(entity, Line):
            document.ksLineSeg(entity.start.x, -entity.start.y, entity.end.x, -entity.end.y, 1)
        elif isinstance(entity, Circle):
            document.ksCircle(entity.center.x, -entity.center.y, entity.radius, 1)
        elif isinstance(entity, Arc):
            document.ksArcByAngle(
                entity.center.x,
                -entity.center.y,
                entity.radius,
                -entity.start_angle,
                -entity.end_angle,
                1,
                1,
            )
        elif isinstance(entity, Polyline):
            pts = list(entity.points)
            for first, second in zip(pts, pts[1:]):
                document.ksLineSeg(first.x, -first.y, second.x, -second.y, 1)
            if entity.closed and len(pts) > 1:
                document.ksLineSeg(pts[-1].x, -pts[-1].y, pts[0].x, -pts[0].y, 1)
        elif isinstance(entity, Text):
            try:
                paragraph = document.ksParagraph(entity.position.x, -entity.position.y, 0, entity.size, 0)
                paragraph.ksTextLine(entity.value, 0)
                paragraph.ksEndObj()
            except Exception:
                # Text is auxiliary in these previews; geometry export must not fail because
                # a specific KOMPAS version exposes a different text API signature.
                continue


def export_to_kompas(drawing: Drawing) -> None:
    """Create the drawing in KOMPAS-3D through its COM 2D API.

    The function uses API5 ksDocument2D primitives for geometry, but it can
    create the document through API7 when a KOMPAS installation does not expose
    KompasObject.Document2D via late-bound COM.
    """
    try:
        import win32com.client
    except ImportError as exc:
        raise RuntimeError("Для экспорта в КОМПАС-3D установите pywin32 и запустите программу в Windows.") from exc

    try:
        kompas = _dispatch_kompas_api5(win32com.client)
    except Exception as exc:  # noqa: BLE001 - COM raises many implementation-specific exceptions.
        raise RuntimeError("Не удалось подключиться к COM API КОМПАС-3D (KOMPAS.Application.5).") from exc

    try:
        kompas.Visible = True
        document = _create_document2d(kompas, win32com.client)
        _draw_to_kompas_document(document, drawing)
    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001 - return a readable message to pywebview instead of a raw COM traceback.
        raise RuntimeError(f"Ошибка построения чертежа в КОМПАС-3D: {exc}") from exc
