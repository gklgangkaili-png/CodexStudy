from game_demo_automation.maa_runtime_720p_v3 import (
    foreground_screencap_method,
    require_maa_720p,
)


class FakeController:
    def __init__(self): self.calls = []
    def set_screenshot_use_raw_size(self, value): self.calls.append(("raw", value)); return True
    def set_screenshot_target_short_side(self, value): self.calls.append(("short", value)); return True


def test_maa_720p_coordinate_space_is_explicit():
    controller = FakeController(); require_maa_720p(controller)
    assert controller.calls == [("raw", False), ("short", 720)]


def test_foreground_screencap_uses_screendc_without_dxgi_fallback_noise():
    class FakeMethods:
        ScreenDC = object()
        Foreground = object()

    assert foreground_screencap_method(FakeMethods) is FakeMethods.ScreenDC
