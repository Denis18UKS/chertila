from chertila.app import ChertilaApi, build_html


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
