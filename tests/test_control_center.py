import json

from game_demo_automation.control_center import discover_recordings
from game_demo_automation.models import Demonstration, StateMarker, WindowIdentity


def _save_demo(path, name: str) -> None:
    path.parent.mkdir(parents=True)
    Demonstration(
        name=name,
        window=WindowIdentity("Simulator", "python.exe", 100, 100),
        events=[],
        states=[
            StateMarker(0, "start", "start.png", (0, 0, 10, 10)),
            StateMarker(100, "end", "end.png", (0, 0, 10, 10)),
        ],
    ).save(path)


def test_discover_recordings_finds_valid_demos_and_skips_invalid(tmp_path) -> None:
    older = tmp_path / "older" / "demonstration.json"
    newer = tmp_path / "newer" / "demonstration.json"
    _save_demo(older, "older")
    _save_demo(newer, "newer")
    older.touch()
    newer.touch()
    invalid = tmp_path / "bad" / "demonstration.json"
    invalid.parent.mkdir()
    invalid.write_text(json.dumps({"bad": True}), encoding="utf-8")
    found = discover_recordings(tmp_path)
    assert set(found) == {older, newer}
