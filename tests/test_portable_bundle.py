import json

from PySide6.QtGui import QColor, QImage

from game_demo_automation.models import Demonstration, InputEvent, StateMarker, WindowIdentity
from game_demo_automation.portable_bundle import write_portable_task_bundle


def _image(path, color: str) -> None:
    image = QImage(100, 80, QImage.Format.Format_RGB32)
    image.fill(QColor(color))
    assert image.save(str(path), "PNG")


def test_portable_bundle_crops_templates_and_uses_relative_names(tmp_path) -> None:
    first = tmp_path / "first-full.png"
    second = tmp_path / "second-full.png"
    _image(first, "red")
    _image(second, "blue")
    demo = Demonstration(
        name="portable",
        window=WindowIdentity("Game Demo Studio - Simulator", "python.exe", 100, 80),
        events=[InputEvent(50, "mouse_click", x=30, y=40)],
        states=[
            StateMarker(0, "start", str(first), (10, 10, 30, 20)),
            StateMarker(100, "end", str(second), (20, 20, 40, 30)),
        ],
        calibrated=True,
    )
    bundle = write_portable_task_bundle(demo, tmp_path / "bundle")
    pipeline = json.loads((bundle / "pipeline" / "main.json").read_text(encoding="utf-8"))
    assert pipeline["state_000_start"]["recognition"]["param"]["template"] == "state_000.png"
    cropped = QImage(str(bundle / "image" / "state_000.png"))
    assert (cropped.width(), cropped.height()) == (30, 20)
