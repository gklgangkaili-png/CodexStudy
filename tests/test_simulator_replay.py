import pytest

from game_demo_automation.models import Demonstration, StateMarker, WindowIdentity
from game_demo_automation.simulator_replay import prepare_simulator_bundle


def _demo(path, *, title="Game Demo Studio - Simulator", calibrated=True) -> None:
    demonstration = Demonstration(
        name="simulator",
        window=WindowIdentity(title, "python.exe", 100, 80),
        events=[],
        states=[
            StateMarker(0, "start", str(path.parent / "start.png"), (0, 0, 10, 10)),
            StateMarker(100, "end", str(path.parent / "end.png"), (0, 0, 10, 10)),
        ],
        calibrated=calibrated,
    )
    demonstration.save(path)


def test_simulator_replay_refuses_other_windows(tmp_path) -> None:
    path = tmp_path / "demo.json"
    _demo(path, title="Some Real Game")
    with pytest.raises(RuntimeError, match="只允许"):
        prepare_simulator_bundle(path)


def test_simulator_replay_requires_calibration(tmp_path) -> None:
    path = tmp_path / "demo.json"
    _demo(path, calibrated=False)
    with pytest.raises(RuntimeError, match="校准"):
        prepare_simulator_bundle(path)
