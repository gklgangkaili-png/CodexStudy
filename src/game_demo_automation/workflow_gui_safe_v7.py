from __future__ import annotations

import ctypes
from pathlib import Path

from . import maa_runtime
from .maa_runtime_720p_v3 import Maa720pForegroundRunner
from .region_bundle_calibrated_v3 import write_calibrated_region_bundle
from .shared_emergency_stop_v2 import SharedF12EmergencyStop
from .task_library import TaskLibrary


ASPECT_SIZES = {"16:9": (1280, 720), "4:3": (960, 720)}


def choose_aspect_ratio() -> str | None:
    """Use a native dialog before Qt owns the GUI event loop."""
    result = ctypes.windll.user32.MessageBoxW(
        None,
        "选择录制比例：\n\n是（Yes）= 16:9，固定 1280×720\n"
        "否（No）= 4:3，固定 960×720\n取消（Cancel）= 退出",
        "选择 Maa 录制比例",
        0x00000003 | 0x00000020,
    )
    if result == 6:
        return "16:9"
    if result == 7:
        return "4:3"
    return None


def _load_gui(aspect: str) -> dict:
    width, height = ASPECT_SIZES[aspect]
    v5_path = Path(__file__).with_name("workflow_gui_safe_v5.py")
    source = v5_path.read_text(encoding="utf-8")
    source = source.replace("959 if cursor.x()", f"{width - 1} if cursor.x()")
    source = source.replace("719 if cursor.y()", f"{height - 1} if cursor.y()")
    source = source.replace("local.width() != 960", f"local.width() != {width}")
    source = source.replace("local.height() != 720", f"local.height() != {height}")
    source = source.replace("960×720", f"{width}×{height}")
    holder = {
        "__name__": "game_demo_automation.workflow_gui_v7_loader",
        "__package__": "game_demo_automation",
        "__file__": str(v5_path),
    }
    exec(compile(source, str(v5_path), "exec"), holder)
    return holder["_upgraded_gui_namespace"]()


def main() -> None:
    aspect = choose_aspect_ratio()
    if aspect is None:
        return
    width, height = ASPECT_SIZES[aspect]
    maa_runtime.EmergencyStopHotkey = SharedF12EmergencyStop
    from PySide6.QtWidgets import QFileDialog

    namespace = _load_gui(aspect)
    original_resolver = namespace["resolve_region_target"]

    def resolve_standard_target(region):
        target = original_resolver(region)
        actual = (target.window.client_width, target.window.client_height)
        if actual != (width, height):
            raise ValueError(
                f"请先把游戏客户区设置为 {width}×{height}（{aspect}）；"
                f"当前为 {actual[0]}×{actual[1]}"
            )
        if target.client_roi != (0, 0, width, height):
            raise ValueError(f"录制框必须与 {width}×{height} 游戏客户区完全重合")
        return target

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

    namespace["resolve_region_target"] = resolve_standard_target
    namespace["MaaForegroundRunner"] = Maa720pForegroundRunner
    namespace["write_region_task_bundle"] = choose_and_write
    namespace["discover_task_bundles"] = lambda _root: library.list(default_tasks)
    namespace["main"]()


if __name__ == "__main__":
    main()
