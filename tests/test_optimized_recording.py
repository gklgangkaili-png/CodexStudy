from game_demo_automation.optimized_recording_v10 import (
    OPTIMIZED_FPS,
    STATE_MINIMUM_GAP_MS,
)


def test_recording_profile_is_bounded_for_long_demonstrations() -> None:
    assert OPTIMIZED_FPS == 3
    assert STATE_MINIMUM_GAP_MS == 1500
    assert 60_000 // STATE_MINIMUM_GAP_MS + 1 <= 41
