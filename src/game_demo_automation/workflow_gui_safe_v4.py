from __future__ import annotations

from pathlib import Path

from . import maa_runtime
from .maa_runtime_raw_v2 import MaaRawForegroundRunner
from .shared_emergency_stop_v2 import SharedF12EmergencyStop
from .task_library import TaskLibrary


def main() -> None:
    maa_runtime.EmergencyStopHotkey = SharedF12EmergencyStop

    from PySide6.QtWidgets import QFileDialog

    from . import workflow_gui

    original_writer = workflow_gui.write_region_task_bundle
    workspace = Path.cwd()
    default_tasks = workspace / "tasks"
    library = TaskLibrary(workspace / ".game-demo-task-library.json")

    def choose_and_write(demo, proposed_destination):
        initial = library.last_parent(default_tasks)
        selected = QFileDialog.getExistingDirectory(
            None,
            "选择 Maa 任务包保存目录",
            str(initial),
            QFileDialog.Option.ShowDirsOnly,
        )
        if not selected:
            raise OSError("已取消导出")
        destination = Path(selected) / Path(proposed_destination).name
        bundle = original_writer(demo, destination)
        library.register(bundle)
        return bundle

    workflow_gui.MaaForegroundRunner = MaaRawForegroundRunner
    workflow_gui.write_region_task_bundle = choose_and_write
    workflow_gui.discover_task_bundles = lambda _root: library.list(default_tasks)
    workflow_gui.main()


if __name__ == "__main__":
    main()
