from dataclasses import dataclass

import pytest

from game_demo_automation.maa_runtime import LiveWindow, select_exact_window, validate_live_window
from game_demo_automation.models import WindowIdentity


@dataclass
class FakeWindow:
    hwnd: int
    window_name: str


def test_window_selection_requires_one_exact_title() -> None:
    selected = select_exact_window([FakeWindow(1, "Other"), FakeWindow(2, "Target")], "Target")
    assert selected.hwnd == 2
    with pytest.raises(RuntimeError, match="找不到"):
        select_exact_window([], "Target")
    with pytest.raises(RuntimeError, match="同名"):
        select_exact_window([FakeWindow(1, "Target"), FakeWindow(2, "Target")], "Target")


def test_live_window_validation_checks_identity_size_and_foreground() -> None:
    expected = WindowIdentity("Target", "game.exe", 960, 540)
    valid = LiveWindow(1, "Target", "GAME.EXE", 960, 540, True)
    assert validate_live_window(expected, valid) == []
    invalid = LiveWindow(1, "Wrong", "other.exe", 800, 600, False)
    assert validate_live_window(expected, invalid) == [
        "窗口标题不匹配",
        "窗口进程不匹配",
        "客户区分辨率不匹配",
        "目标窗口不在前台",
    ]
