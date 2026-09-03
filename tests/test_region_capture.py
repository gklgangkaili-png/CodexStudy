from game_demo_automation.models import InputEvent, WindowIdentity
from game_demo_automation.region_capture import RegionTarget, ScreenRegion, derive_state_times


def test_region_target_converts_screen_to_client_coordinates() -> None:
    target = RegionTarget(
        hwnd=1,
        window=WindowIdentity("Game", "game.exe", 800, 600),
        client_origin_x=100,
        client_origin_y=50,
        screen_region=ScreenRegion(140, 90, 300, 200),
    )
    assert target.client_roi == (40, 40, 300, 200)
    assert target.screen_to_client(200, 150) == (100, 100)


def test_state_times_use_frames_before_actions_and_keep_final_state() -> None:
    events = [
        InputEvent(410, "mouse_click", x=1, y=1),
        InputEvent(920, "key_down", key=0x57),
    ]
    assert derive_state_times(events, [0, 400, 800, 1200]) == [0, 400, 800, 1200]
