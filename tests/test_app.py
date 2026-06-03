from pathlib import Path

from chertila.app import ChertilaApi, _set_active_window, build_html


class FakeWindow:
    def __init__(self, path: Path) -> None:
        self.path = path

    def create_file_dialog(self, *_args, **_kwargs):
        return str(self.path)


def test_pywebview_html_contains_controls() -> None:
    html = build_html()
    assert "pywebview" in html
    assert "Экспорт SVG" in html
    assert "Построить в КОМПАС-3D" in html


def test_api_state_switches_selected_drawing() -> None:
    api = ChertilaApi()
    state = api.get_state()
    assert state["drawings"]
    last_key = state["drawings"][-1]
    switched = api.select_drawing(last_key)
    assert switched["selected"] == last_key
    assert switched["orientation"] == "vertical"
    assert "<svg" in switched["svg"]


def test_api_does_not_expose_native_window_to_pywebview() -> None:
    api = ChertilaApi()
    assert not hasattr(api, "window")
    assert all(name.startswith("_") or callable(getattr(api, name)) for name in dir(api))


def test_api_export_uses_module_level_window(tmp_path: Path) -> None:
    output = tmp_path / "preview"
    _set_active_window(FakeWindow(output))
    state = ChertilaApi().export_svg()
    assert output.with_suffix(".svg").exists()
    assert "SVG сохранён" in state["status"]
