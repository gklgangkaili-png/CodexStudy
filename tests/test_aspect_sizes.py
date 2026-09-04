from game_demo_automation.workflow_gui_safe_v7 import ASPECT_SIZES


def test_supported_aspects_use_maa_short_side_720() -> None:
    assert ASPECT_SIZES == {"16:9": (1280, 720), "4:3": (960, 720)}
    assert all(height == 720 for _width, height in ASPECT_SIZES.values())
