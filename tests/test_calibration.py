from game_demo_automation.calibration import CalibrationDocument
from game_demo_automation.models import Demonstration, StateMarker, WindowIdentity


def test_editing_invalidates_and_approval_calibrates() -> None:
    demo = Demonstration(
        name="demo",
        window=WindowIdentity("Simulator", "python.exe", 100, 100),
        events=[],
        states=[
            StateMarker(0, "start", "start.png", (0, 0, 10, 10)),
            StateMarker(100, "end", "end.png", (0, 0, 10, 10)),
        ],
        calibrated=True,
    )
    document = CalibrationDocument(demo)
    document.update_state(0, threshold=0.9)
    assert demo.calibrated is False
    assert demo.states[0].threshold == 0.9
    document.approve()
    assert demo.calibrated is True
