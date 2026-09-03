from game_demo_automation.models import Demonstration, StateMarker, WindowIdentity
from game_demo_automation.safety import RuntimeSnapshot, preflight_errors


def make_demo() -> Demonstration:
    window = WindowIdentity("Simulator", "simulator.exe", 960, 540)
    return Demonstration(
        name="safe demo",
        window=window,
        events=[],
        states=[
            StateMarker(0, "start", "start.png", (0, 0, 100, 100)),
            StateMarker(1000, "end", "end.png", (0, 0, 100, 100)),
        ],
        calibrated=True,
    )


def test_preflight_accepts_matching_safe_runtime() -> None:
    demo = make_demo()
    assert preflight_errors(demo, RuntimeSnapshot(demo.window, True, True, True)) == []


def test_preflight_rejects_focus_state_hotkey_and_pressed_keys() -> None:
    demo = make_demo()
    errors = preflight_errors(
        demo, RuntimeSnapshot(demo.window, False, False, False, frozenset({0x57}))
    )
    assert len(errors) == 4
    assert "目标窗口不在前台" in errors
