from game_demo_automation.models import StateMarker
from game_demo_automation.workflow_gui_safe_v9 import (
    DEFAULT_TEMPLATE_THRESHOLD,
    _set_new_state_default,
)


def test_new_state_threshold_is_point_five() -> None:
    original = StateMarker.__init__.__defaults__
    try:
        _set_new_state_default()
        state = StateMarker(0, "ready", "ready.png", (0, 0, 10, 10))
        assert state.threshold == DEFAULT_TEMPLATE_THRESHOLD == 0.5
    finally:
        StateMarker.__init__.__defaults__ = original
