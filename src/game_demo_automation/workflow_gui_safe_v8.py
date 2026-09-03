from __future__ import annotations

import ctypes
from ctypes import wintypes
from pathlib import Path

from . import maa_runtime
from .maa_runtime_720p_v3 import Maa720pForegroundRunner
from .region_bundle_calibrated_v3 import write_calibrated_region_bundle
from .shared_emergency_stop_v2 import SharedF12EmergencyStop
from .task_library import TaskLibrary
from .workflow_gui_safe_v7 import ASPECT_SIZES, _load_gui, choose_aspect_ratio


def client_region_under_center(region, screen_region_type):
    """Snap an approximate selection to the underlying Win32 client rectangle."""
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    point = wintypes.POINT(region.x + region.width // 2, region.y + region.height // 2)
    hwnd = user32.GetAncestor(user32.WindowFromPoint(point), 2)
    if not hwnd:
        raise ValueError("选择位置下方没有可控制的窗口")
    rect = wintypes.RECT()
    origin = wintypes.POINT(0, 0)
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise OSError(ctypes.get_last_error(), "GetClientRect failed")
    if not user32.ClientToScreen(hwnd, ctypes.byref(origin)):
        raise OSError(ctypes.get_last_error(), "ClientToScreen failed")
    return screen_region_type(
        origin.x,
        origin.y,
        rect.right - rect.left,
        rect.bottom - rect.top,
    )


def main() -> None:
    aspect = choose_aspect_ratio()
    if aspect is None:
        return
    width, height = ASPECT_SIZES[aspect]
    maa_runtime.EmergencyStopHotkey = SharedF12EmergencyStop
    from PySide6.QtWidgets import QFileDialog

    namespace = _load_gui(aspect)
    original_resolver = namespace["resolve_region_target"]
    screen_region_type = namespace["ScreenRegion"]

    def resolve_snapped_target(approximate_region):
        snapped = client_region_under_center(approximate_region, screen_region_type)
        actual = (snapped.width, snapped.height)
        if actual != (width, height):
            raise ValueError(
                f"已找到目标窗口，但客户区为 {actual[0]}×{actual[1]}；"
                f"请设置为 {width}×{height}（{aspect}）后重试"
            )
        return original_resolver(snapped)

    workspace = Path.cwd()
    default_tasks = workspace / "tasks"
    library = TaskLibrary(workspace / ".game-demo-task-library.json")

    def choose_and_write(demo, proposed_destination):
        selected = QFileDialog.getExistingDirectory(
            None,
            "选择 Maa 任务包保存目录",
            str(library.last_parent(default_tasks)),
            QFileDialog.Option.ShowDirsOnly,
        )
        if not selected:
            raise OSError("已取消导出")
        destination = Path(selected) / Path(proposed_destination).name
        bundle = write_calibrated_region_bundle(demo, destination)
        library.register(bundle)
        return bundle

    namespace["resolve_region_target"] = resolve_snapped_target
    namespace["MaaForegroundRunner"] = Maa720pForegroundRunner
    namespace["write_region_task_bundle"] = choose_and_write
    namespace["discover_task_bundles"] = lambda _root: library.list(default_tasks)
    namespace["main"]()


if __name__ == "__main__":
    main()
