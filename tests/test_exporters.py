from pathlib import Path

from chertila.exporters import drawing_to_svg, save_dxf, save_svg
from chertila.model import Circle, Polyline
from chertila.variants import (
    all_drawings,
    screenshot_1_variant_14,
    screenshot_2_variant_14,
    screenshot_3_variant_14_vertical,
)


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


def test_first_screenshot_is_variant_14_without_hexagon_insert() -> None:
    drawing = screenshot_1_variant_14()
    closed_polylines = [
        entity for entity in drawing.entities if isinstance(entity, Polyline) and entity.closed
    ]
    solid_circles = [entity for entity in drawing.entities if isinstance(entity, Circle)]
    assert all(len(polyline.points) != 6 for polyline in closed_polylines)
    assert len(solid_circles) == 2
    assert {circle.radius for circle in solid_circles} == {30, 40}


def test_updated_reference_dimensions_are_present() -> None:
    second_svg = drawing_to_svg(screenshot_2_variant_14())
    third_svg = drawing_to_svg(screenshot_3_variant_14_vertical())
    assert "120" in second_svg
    assert "⌀110" in second_svg
    assert "60" in third_svg
    assert "120" in third_svg
    assert "R90" in third_svg


class FakeDocumentParam:
    def __init__(self) -> None:
        self.type = None
        self.regime = None


class FakeKompasDocument:
    def __init__(self) -> None:
        self.created_with = None
        self.lines: list[tuple[float, ...]] = []

    def ksCreateDocument(self, document_param: FakeDocumentParam) -> bool:
        self.created_with = document_param
        return True

    def ksLineSeg(self, *args) -> None:
        self.lines.append(args)

    def ksCircle(self, *_args) -> None:
        pass

    def ksArcByAngle(self, *_args) -> None:
        pass

    def ksParagraph(self, *_args):
        raise AttributeError("text API not available in fake")


class FakeKompasApi5:
    def __init__(self, document_available: bool = True) -> None:
        self.document = FakeKompasDocument()
        self.document_param = FakeDocumentParam()
        self.document_available = document_available
        self.application7 = FakeApplication7()

    def Document2D(self) -> FakeKompasDocument:
        if not self.document_available:
            raise AttributeError("Document2D")
        return self.document

    def ActiveDocument2D(self) -> FakeKompasDocument:
        return self.document

    def GetParamStruct(self, struct_type: int) -> FakeDocumentParam:
        assert struct_type == 35
        return self.document_param

    def ksGetApplication7(self):
        return self.application7


class FakeApplication7:
    def __init__(self) -> None:
        self.Visible = False
        self.Documents = FakeDocuments()


class FakeDocuments:
    def __init__(self) -> None:
        self.add_calls: list[tuple] = []

    def Add(self, *args) -> None:
        self.add_calls.append(args)


class FakeWin32Client:
    def Dispatch(self, *_args):
        return FakeApplication7()


def test_kompas_document_creation_uses_document_param() -> None:
    from chertila.exporters import _create_document2d

    kompas = FakeKompasApi5()
    document = _create_document2d(kompas, FakeWin32Client())
    assert document is kompas.document
    assert document.created_with is kompas.document_param
    assert kompas.document_param.type == 1
    assert kompas.document_param.regime == 0


def test_kompas_document_creation_falls_back_to_api7() -> None:
    from chertila.exporters import _create_document2d

    kompas = FakeKompasApi5(document_available=False)
    document = _create_document2d(kompas, FakeWin32Client())
    assert document is kompas.document
    assert kompas.application7.Visible is True
    assert kompas.application7.Documents.add_calls[0] == (1, True)
