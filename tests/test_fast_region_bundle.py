import json

from PySide6.QtGui import QImage

from game_demo_automation.models import Demonstration, StateMarker, WindowIdentity
from game_demo_automation.region_bundle_fast_v9 import write_fast_region_bundle


def test_unchanged_template_uses_byte_identical_fast_path(tmp_path) -> None:
    recording = tmp_path / "recording"; templates = recording / "templates"; templates.mkdir(parents=True)
    source = templates / "state.png"; image = QImage(20, 10, QImage.Format.Format_RGB32); image.fill(0x123456); image.save(str(source), "PNG")
    (recording / "region.json").write_text(json.dumps({"client_roi": [0, 0, 20, 10]}), encoding="utf-8")
    states = [StateMarker(0, "a", str(source), (0, 0, 20, 10)), StateMarker(1, "b", str(source), (0, 0, 20, 10))]
    demo = Demonstration("fast", WindowIdentity("Game", "game.exe", 20, 10), [], states, calibrated=True)
    output = write_fast_region_bundle(demo, tmp_path / "out")
    assert (output / "image" / "state_000.png").read_bytes() == source.read_bytes()
