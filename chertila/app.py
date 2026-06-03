from __future__ import annotations

from pathlib import Path
from typing import Any

from .exporters import drawing_to_svg, export_to_kompas, save_dxf, save_svg
from .model import Drawing
from .variants import all_drawings


class ChertilaApi:
    """Small pywebview bridge used by the HTML interface."""

    def __init__(self) -> None:
        self.drawings = all_drawings()
        self.selected_key = next(iter(self.drawings))
        self.reference_path = ""
        self.status = "Выберите схему варианта 14 и экспортируйте SVG/DXF или в КОМПАС-3D."
        self.window: Any | None = None

    def set_window(self, window: Any) -> None:
        self.window = window

    @property
    def drawing(self) -> Drawing:
        return self.drawings[self.selected_key]

    def get_state(self) -> dict[str, Any]:
        return {
            "drawings": list(self.drawings),
            "selected": self.selected_key,
            "orientation": self.drawing.orientation,
            "referencePath": self.reference_path,
            "status": self.status,
            "svg": drawing_to_svg(self.drawing),
        }

    def select_drawing(self, key: str) -> dict[str, Any]:
        if key not in self.drawings:
            self.status = f"Схема не найдена: {key}"
            return self.get_state()
        self.selected_key = key
        self.status = f"Открыта схема: {key} ({self.drawing.orientation})."
        return self.get_state()

    def choose_reference(self) -> dict[str, Any]:
        if self.window is None:
            self.status = "Окно pywebview ещё не готово."
            return self.get_state()

        import webview

        paths = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("Images (*.png;*.jpg;*.jpeg;*.bmp;*.gif)", "All files (*.*)"),
        )
        if paths:
            self.reference_path = str(Path(paths[0]).name)
            self.status = f"Референс добавлен: {paths[0]}"
        return self.get_state()

    def export_svg(self) -> dict[str, Any]:
        return self._export_file("svg")

    def export_dxf(self) -> dict[str, Any]:
        return self._export_file("dxf")

    def export_kompas(self) -> dict[str, Any]:
        try:
            export_to_kompas(self.drawing)
        except RuntimeError as exc:
            self.status = str(exc)
        else:
            self.status = "Чертёж передан в КОМПАС-3D."
        return self.get_state()

    def _export_file(self, extension: str) -> dict[str, Any]:
        if self.window is None:
            self.status = "Окно pywebview ещё не готово."
            return self.get_state()

        import webview

        file_type = "SVG (*.svg)" if extension == "svg" else "DXF (*.dxf)"
        path = self.window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=f"{self.drawing.name}.{extension}",
            file_types=(file_type, "All files (*.*)"),
        )
        if not path:
            return self.get_state()

        output = Path(path if isinstance(path, str) else path[0])
        if output.suffix.lower() != f".{extension}":
            output = output.with_suffix(f".{extension}")
        if extension == "svg":
            save_svg(self.drawing, output)
        else:
            save_dxf(self.drawing, output)
        self.status = f"{extension.upper()} сохранён: {output}"
        return self.get_state()


def build_html() -> str:
    return """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Chertila — КОМПАС-3D</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, "Segoe UI", Arial, sans-serif;
      --bg: #f3f6fb;
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #64748b;
      --accent: #2563eb;
      --accent-dark: #1d4ed8;
      --border: #d8dee9;
    }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--text); }
    .app { display: grid; grid-template-columns: 360px 1fr; gap: 18px; min-height: 100vh; padding: 18px; }
    .panel, .preview { background: var(--panel); border: 1px solid var(--border); border-radius: 18px; box-shadow: 0 12px 30px rgba(15, 23, 42, .08); }
    .panel { padding: 22px; }
    .preview { display: flex; flex-direction: column; min-width: 0; overflow: hidden; }
    h1 { margin: 0 0 6px; font-size: 24px; }
    .subtitle { margin: 0 0 22px; color: var(--muted); line-height: 1.45; }
    label { display: block; margin-bottom: 8px; font-weight: 700; }
    select { width: 100%; padding: 11px 12px; border: 1px solid var(--border); border-radius: 10px; background: white; font: inherit; }
    .buttons { display: grid; gap: 10px; margin: 20px 0; }
    button { border: 0; border-radius: 11px; padding: 12px 14px; background: var(--accent); color: white; font-weight: 800; cursor: pointer; transition: .15s ease; }
    button:hover { background: var(--accent-dark); transform: translateY(-1px); }
    button.secondary { background: #e8eefc; color: var(--accent-dark); }
    button.secondary:hover { background: #dbe7ff; }
    .info { border-top: 1px solid var(--border); padding-top: 18px; color: var(--muted); line-height: 1.5; }
    .badge { display: inline-block; margin: 10px 0 0; padding: 5px 9px; border-radius: 999px; background: #ecfdf5; color: #047857; font-weight: 700; font-size: 13px; }
    .reference { overflow-wrap: anywhere; color: var(--text); font-weight: 700; }
    .toolbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 14px 18px; border-bottom: 1px solid var(--border); }
    .status { color: var(--muted); font-size: 14px; }
    .canvas { flex: 1; display: grid; place-items: center; min-height: 0; padding: 18px; background: linear-gradient(45deg, #f8fafc 25%, transparent 25%), linear-gradient(-45deg, #f8fafc 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #f8fafc 75%), linear-gradient(-45deg, transparent 75%, #f8fafc 75%); background-size: 24px 24px; background-position: 0 0, 0 12px, 12px -12px, -12px 0; }
    .sheet { max-width: 100%; max-height: 100%; padding: 16px; background: white; border: 1px solid var(--border); box-shadow: 0 8px 20px rgba(15, 23, 42, .1); overflow: auto; }
    .sheet svg { display: block; max-width: 100%; height: auto; }
    @media (max-width: 860px) { .app { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main class="app">
    <aside class="panel">
      <h1>Chertila</h1>
      <p class="subtitle">Генератор чертежей варианта 14 с интерфейсом pywebview и экспортом в КОМПАС-3D.</p>
      <label for="drawingSelect">Схема</label>
      <select id="drawingSelect"></select>
      <div id="orientation" class="badge">orientation</div>
      <div class="buttons">
        <button class="secondary" id="referenceButton">Добавить скриншот-референс</button>
        <button id="svgButton">Экспорт SVG</button>
        <button id="dxfButton">Экспорт DXF</button>
        <button id="kompasButton">Построить в КОМПАС-3D</button>
      </div>
      <div class="info">
        <p>1-й и 2-й скриншоты строятся горизонтально, 3-й — вертикально.</p>
        <p>Референс: <span id="reference" class="reference">не выбран</span></p>
        <p>Для прямого экспорта нужен Windows, установленный КОМПАС-3D и pywin32.</p>
      </div>
    </aside>
    <section class="preview">
      <div class="toolbar">
        <strong>Предпросмотр чертежа</strong>
        <span id="status" class="status"></span>
      </div>
      <div class="canvas"><div id="sheet" class="sheet"></div></div>
    </section>
  </main>
<script>
  let currentState = null;

  function apiReady() {
    return window.pywebview && window.pywebview.api;
  }

  async function callApi(method, ...args) {
    if (!apiReady()) {
      document.getElementById('status').textContent = 'pywebview API ещё загружается...';
      return;
    }
    const state = await window.pywebview.api[method](...args);
    render(state);
  }

  function render(state) {
    currentState = state;
    const select = document.getElementById('drawingSelect');
    if (select.options.length === 0) {
      state.drawings.forEach((name) => {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = name;
        select.appendChild(option);
      });
    }
    select.value = state.selected;
    document.getElementById('orientation').textContent = state.orientation === 'vertical' ? 'вертикально' : 'горизонтально';
    document.getElementById('reference').textContent = state.referencePath || 'не выбран';
    document.getElementById('status').textContent = state.status;
    document.getElementById('sheet').innerHTML = state.svg;
  }

  window.addEventListener('pywebviewready', () => callApi('get_state'));
  window.addEventListener('DOMContentLoaded', () => {
    document.getElementById('drawingSelect').addEventListener('change', (event) => callApi('select_drawing', event.target.value));
    document.getElementById('referenceButton').addEventListener('click', () => callApi('choose_reference'));
    document.getElementById('svgButton').addEventListener('click', () => callApi('export_svg'));
    document.getElementById('dxfButton').addEventListener('click', () => callApi('export_dxf'));
    document.getElementById('kompasButton').addEventListener('click', () => callApi('export_kompas'));
  });
</script>
</body>
</html>
"""


def main() -> None:
    import webview

    api = ChertilaApi()
    window = webview.create_window(
        "Chertila — генератор чертежей для КОМПАС-3D",
        html=build_html(),
        js_api=api,
        width=1100,
        height=760,
        min_size=(860, 620),
    )
    api.set_window(window)
    webview.start(debug=False)


if __name__ == "__main__":
    main()
