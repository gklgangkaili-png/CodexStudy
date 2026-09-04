from __future__ import annotations

from pathlib import Path

from . import maa_runtime
from .maa_runtime_720p_v3 import Maa720pForegroundRunner
from .region_bundle_calibrated_v3 import write_calibrated_region_bundle
from .shared_emergency_stop_v2 import SharedF12EmergencyStop
from .task_library import TaskLibrary


def _upgraded_gui_namespace() -> dict:
    """Load the stable GUI while applying v5 UI changes in memory."""
    source_path = Path(__file__).with_name("workflow_gui.py")
    source = source_path.read_text(encoding="utf-8")
    source = source.replace(
        "self.end_point = event.position().toPoint()",
        """cursor = event.position().toPoint()
                self.end_point = self.start_point + QPoint(
                    959 if cursor.x() >= self.start_point.x() else -959,
                    719 if cursor.y() >= self.start_point.y() else -719,
                )""",
    )
    source = source.replace(
        'if local.width() < 40 or local.height() < 40:\n                QMessageBox.warning(self, "区域过小", "请至少框选 40×40 像素区域")',
        'if local.width() != 960 or local.height() != 720:\n                QMessageBox.warning(self, "区域无效", "录制框固定为 Maa 4:3 标准 960×720")',
    )
    source = source.replace(
        '"拖动鼠标选择录制区域，按 Esc 取消"',
        '"拖动定位固定 960×720 Maa 录制框，按 Esc 取消"',
    )
    source = source.replace(
        "    class CalibrationDialog(QDialog):",
        """    class RoiPreviewLabel(QLabel):
        roi_selected = Signal(object)

        def __init__(self):
            super().__init__()
            self.setMinimumSize(720, 400)
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.start_point = None
            self.end_point = None
            self.base_roi = (0, 0, 0, 0)

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.start_point = event.position().toPoint()
                self.end_point = self.start_point

        def mouseMoveEvent(self, event):
            if self.start_point is not None:
                self.end_point = event.position().toPoint(); self.update()

        def mouseReleaseEvent(self, event):
            if self.start_point is None: return
            self.end_point = event.position().toPoint()
            shown = self.pixmap()
            if shown is None: return
            left = (self.width() - shown.width()) // 2
            top = (self.height() - shown.height()) // 2
            rect = QRect(self.start_point, self.end_point).normalized().translated(-left, -top)
            rect = rect.intersected(QRect(0, 0, shown.width(), shown.height()))
            if rect.width() >= 16 and rect.height() >= 16:
                bx, by, _, _ = self.base_roi
                self.roi_selected.emit((bx + rect.x(), by + rect.y(), rect.width(), rect.height()))
            self.start_point = None; self.update()

        def paintEvent(self, event):
            super().paintEvent(event)
            if self.start_point is not None and self.end_point is not None:
                painter = QPainter(self); painter.setPen(QPen(QColor("#ff4d4f"), 2))
                painter.drawRect(QRect(self.start_point, self.end_point).normalized())

    class CalibrationDialog(QDialog):""",
    )
    source = source.replace(
        "            layout.addWidget(self.table)\n            buttons = QDialogButtonBox(",
        """            self.table.setMaximumHeight(220)
            layout.addWidget(self.table)
            layout.addWidget(QLabel("选择状态后，在下方截图拖框稳定特征（按钮、图标、固定 HUD），不要框整幅动态画面。"))
            self.preview = RoiPreviewLabel()
            self.preview.roi_selected.connect(self.set_visual_roi)
            self.table.currentCellChanged.connect(self.preview_state)
            layout.addWidget(self.preview)
            self.preview_state(0, 0, -1, -1)
            buttons = QDialogButtonBox(""",
    )
    source = source.replace(
        "        def save(self) -> None:\n            try:\n                for row in range(self.table.rowCount()):",
        """        def preview_state(self, row, _column, _old_row, _old_column):
            if row < 0: return
            state = self.document.demonstration.states[row]
            pixmap = QPixmap(state.template)
            self.preview.base_roi = state.roi
            self.preview.setPixmap(pixmap)

        def set_visual_roi(self, roi):
            row = self.table.currentRow()
            if row >= 0:
                self.table.item(row, 2).setText(",".join(map(str, roi)))

        def save(self) -> None:
            try:
                for row in range(self.table.rowCount()):
                    roi = tuple(int(part.strip()) for part in self.table.item(row, 2).text().split(","))
                    if len(roi) != 4: raise ValueError("ROI 必须包含四个整数")""",
    )
    source = source.replace(
        "                        name=self.table.item(row, 0).text().strip(),\n                        threshold=",
        "                        name=self.table.item(row, 0).text().strip(),\n                        roi=roi,\n                        threshold=",
    )
    namespace = {
        "__name__": "game_demo_automation.workflow_gui_v5_runtime",
        "__package__": "game_demo_automation",
        "__file__": str(source_path),
    }
    exec(compile(source, str(source_path), "exec"), namespace)
    return namespace


def main() -> None:
    maa_runtime.EmergencyStopHotkey = SharedF12EmergencyStop
    from PySide6.QtWidgets import QFileDialog

    namespace = _upgraded_gui_namespace()
    workspace = Path.cwd()
    default_tasks = workspace / "tasks"
    library = TaskLibrary(workspace / ".game-demo-task-library.json")

    def choose_and_write(demo, proposed_destination):
        selected = QFileDialog.getExistingDirectory(
            None, "选择 Maa 任务包保存目录", str(library.last_parent(default_tasks)),
            QFileDialog.Option.ShowDirsOnly,
        )
        if not selected:
            raise OSError("已取消导出")
        bundle = write_calibrated_region_bundle(demo, Path(selected) / Path(proposed_destination).name)
        library.register(bundle)
        return bundle

    namespace["MaaForegroundRunner"] = Maa720pForegroundRunner
    namespace["write_region_task_bundle"] = choose_and_write
    namespace["discover_task_bundles"] = lambda _root: library.list(default_tasks)
    namespace["main"]()


if __name__ == "__main__":
    main()
