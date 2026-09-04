from __future__ import annotations

from pathlib import Path

from . import maa_runtime
from .maa_runtime_720p_v3 import Maa720pForegroundRunner
from .region_bundle_calibrated_v3 import write_calibrated_region_bundle
from .shared_emergency_stop_v2 import SharedF12EmergencyStop
from .task_library import TaskLibrary
from .workflow_gui_safe_v5 import _upgraded_gui_namespace


def main() -> None:
    maa_runtime.EmergencyStopHotkey = SharedF12EmergencyStop
    from PySide6.QtWidgets import QFileDialog

    namespace = _upgraded_gui_namespace()
    original_resolver = namespace["resolve_region_target"]

    def resolve_standard_target(region):
        target = original_resolver(region)
        actual = (target.window.client_width, target.window.client_height)
        if actual != (960, 720):
            raise ValueError(
                f"请先把游戏客户区设置为 960×720；当前为 {actual[0]}×{actual[1]}"
            )
        if target.client_roi != (0, 0, 960, 720):
            raise ValueError("录制框必须与 960×720 游戏客户区完全重合")
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
