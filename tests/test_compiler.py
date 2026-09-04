import json

import pytest

from game_demo_automation.compiler import compile_demonstration, write_task_bundle
from game_demo_automation.models import Demonstration, InputEvent, StateMarker, WindowIdentity


def demo(calibrated: bool = True) -> Demonstration:
    return Demonstration(
        name="three runs",
        window=WindowIdentity("Simulator", "simulator.exe", 960, 540),
        events=[
            InputEvent(100, "mouse_click", x=480, y=450),
            InputEvent(1100, "key_down", key=0x57),
            InputEvent(2100, "key_up", key=0x57),
        ],
        states=[
            StateMarker(0, "select", "select.png", (0, 0, 960, 160)),
            StateMarker(1000, "battle", "battle.png", (0, 0, 960, 160)),
            StateMarker(2200, "result", "result.png", (0, 0, 960, 160)),
        ],
        calibrated=calibrated,
    )


def test_compiler_builds_state_driven_maa_pipeline() -> None:
    pipeline = compile_demonstration(demo())
    assert pipeline["entry"]["next"] == ["state_000_select"]
    assert pipeline["state_000_select"]["recognition"]["type"] == "TemplateMatch"
    assert pipeline["state_000_select_action_000"]["action"] == {
        "type": "Click",
        "param": {"target": [480, 450]},
    }
    assert pipeline["state_001_battle_action_000"]["action"]["type"] == "KeyDown"
    assert pipeline["state_001_battle_action_001"]["action"]["type"] == "KeyUp"


def test_uncalibrated_demo_is_rejected() -> None:
    with pytest.raises(ValueError, match="calibrated"):
        compile_demonstration(demo(calibrated=False))


def test_task_bundle_contains_pipeline_and_safety_metadata(tmp_path) -> None:
    output = write_task_bundle(demo(), tmp_path / "bundle")
    pipeline = json.loads((output / "pipeline" / "main.json").read_text(encoding="utf-8"))
    safety = json.loads((output / "safety.json").read_text(encoding="utf-8"))
    assert "safe_pause" in pipeline
    assert safety["window"]["client_width"] == 960
    assert safety["calibrated"] is True
