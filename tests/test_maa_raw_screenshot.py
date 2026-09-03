from __future__ import annotations

import pytest

from game_demo_automation.maa_runtime_raw_v2 import require_raw_screenshot


class FakeController:
    def __init__(self, result: bool) -> None:
        self.result = result
        self.calls: list[bool] = []

    def set_screenshot_use_raw_size(self, enable: bool) -> bool:
        self.calls.append(enable)
        return self.result


def test_raw_screenshot_is_forced() -> None:
    controller = FakeController(True)

    require_raw_screenshot(controller)

    assert controller.calls == [True]


def test_raw_screenshot_failure_pauses_safely() -> None:
    controller = FakeController(False)

    with pytest.raises(RuntimeError, match="原始截图尺寸"):
        require_raw_screenshot(controller)
