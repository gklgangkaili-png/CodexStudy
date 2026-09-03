from __future__ import annotations

import random
import sys
from datetime import datetime
from pathlib import Path

from .calibration import CalibrationDocument
from .compiler import write_task_bundle
from .models import WindowIdentity
from .recording import RecordingSession


def main() -> None:
    try:
        from PySide6.QtCore import QBuffer, QIODevice, Qt, QTimer
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtWidgets import (
            QApplication,
            QFileDialog,
            QHBoxLayout,
            QLabel,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QTableWidget,
            QTableWidgetItem,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        raise SystemExit(
            "Install UI dependencies with: py -m pip install --user -e '.[ui]'"
        ) from exc

    class Studio(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Game Demo Studio - Simulator")
            self.setFixedSize(960, 540)
            self.session: RecordingSession | None = None
            self.demo_path: Path | None = None
            self.run_count = 0
            self.state = "select"
            root = QWidget()
            layout = QVBoxLayout(root)
            toolbar = QHBoxLayout()
            self.record_button = QPushButton("开始示教录制")
            self.record_button.clicked.connect(self.toggle_recording)
            self.calibrate_button = QPushButton("校准并导出")
            self.calibrate_button.setEnabled(False)
            self.calibrate_button.clicked.connect(self.open_calibration)
            toolbar.addWidget(self.record_button)
            toolbar.addWidget(self.calibrate_button)
            toolbar.addStretch()
            self.recording_status = QLabel("未录制")
            toolbar.addWidget(self.recording_status)
            self.title = QLabel()
            self.title.setStyleSheet("font-size: 32px; font-weight: bold")
            self.status = QLabel()
            self.status.setStyleSheet("font-size: 20px")
            self.action = QPushButton()
            self.action.setMinimumHeight(72)
            self.action.clicked.connect(self.perform_action)
            failure = QPushButton("注入未示教失败")
            failure.clicked.connect(lambda: self.show_state("failure"))
            layout.addLayout(toolbar)
            layout.addWidget(self.title)
            layout.addWidget(self.status)
            layout.addStretch()
            layout.addWidget(self.action)
            layout.addWidget(failure)
            self.setCentralWidget(root)
            self.frame_timer = QTimer(self)
            self.frame_timer.setInterval(1000 // 15)
            self.frame_timer.timeout.connect(self.record_frame)
            self.show_state("select", record=False)

        def png(self) -> bytes:
            image = self.grab()
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "PNG")
            return bytes(buffer.data())

        def toggle_recording(self) -> None:
            if self.session is None:
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                root = Path.cwd() / "recordings" / stamp
                self.session = RecordingSession(
                    root,
                    WindowIdentity(self.windowTitle(), "python.exe", self.width(), self.height()),
                )
                self.record_button.setText("停止示教录制")
                self.recording_status.setText(f"录制中：{root}")
                self.frame_timer.start()
                QTimer.singleShot(0, lambda: self.record_current_state("select"))
                return
            self.frame_timer.stop()
            session = self.session
            try:
                demo = session.build_demonstration("simulator demonstration")
                self.demo_path = session.root / "demonstration.json"
                self.recording_status.setText(f"已保存：{self.demo_path}")
                self.calibrate_button.setEnabled(True)
                QMessageBox.information(
                    self,
                    "录制完成",
                    f"记录了 {len(demo.states)} 个状态和 {len(demo.events)} 个输入事件。",
                )
            except ValueError as exc:
                QMessageBox.warning(self, "录制不完整", str(exc))
            finally:
                session.close()
                self.session = None
                self.record_button.setText("开始示教录制")

        def record_frame(self) -> None:
            if self.session is not None:
                self.session.record_frame(self.png())

        def record_current_state(self, name: str) -> None:
            if self.session is not None:
                self.session.record_state(name, self.png(), (0, 60, self.width(), 180))

        def show_state(self, state: str, *, record: bool = True) -> None:
            labels = {
                "select": ("STATE: SELECT_LEVEL", "选择固定副本", "开始挑战"),
                "loading": ("STATE: LOADING", "随机加载中……", "请等待"),
                "battle": ("STATE: BATTLE", "按住并释放 W 完成本轮移动", "也可点击完成"),
                "result": ("STATE: RESULT", f"已完成 {self.run_count} 次", "再次挑战"),
                "done": ("STATE: DONE", "示教完成", "重置"),
                "failure": ("STATE: UNKNOWN_FAILURE", "未示教状态应安全暂停", "返回选关"),
            }
            self.state = state
            title, status, action = labels[state]
            self.title.setText(title)
            self.status.setText(status)
            self.action.setText(action)
            self.action.setEnabled(state != "loading")
            if record:
                QTimer.singleShot(0, lambda state=state: self.record_current_state(state))

        def perform_action(self) -> None:
            if self.session is not None:
                point = self.action.geometry().center()
                self.session.record_event("mouse_click", x=point.x(), y=point.y())
            if self.state == "select":
                self.show_state("loading")
                QTimer.singleShot(random.randint(600, 1500), lambda: self.show_state("battle"))
            elif self.state == "battle":
                self.run_count += 1
                self.show_state("result")
            elif self.state == "result":
                if self.run_count >= 3:
                    self.show_state("done")
                else:
                    self.show_state("loading")
                    QTimer.singleShot(random.randint(600, 1500), lambda: self.show_state("battle"))
            elif self.state in {"done", "failure"}:
                self.run_count = 0
                self.show_state("select")

        def keyPressEvent(self, event: QKeyEvent) -> None:
            if self.session is not None and event.key() not in {Qt.Key.Key_Alt, Qt.Key.Key_Tab}:
                self.session.record_event("key_down", key=event.nativeVirtualKey())
            super().keyPressEvent(event)

        def keyReleaseEvent(self, event: QKeyEvent) -> None:
            if self.session is not None and event.key() not in {Qt.Key.Key_Alt, Qt.Key.Key_Tab}:
                self.session.record_event("key_up", key=event.nativeVirtualKey())
            if self.state == "battle" and event.key() == Qt.Key.Key_W:
                self.run_count += 1
                self.show_state("result")
            super().keyReleaseEvent(event)

        def open_calibration(self) -> None:
            if self.demo_path is None:
                return
            document = CalibrationDocument.load(self.demo_path)
            dialog = QMainWindow(self)
            dialog.setWindowTitle("示教校准")
            table = QTableWidget(len(document.demonstration.states), 4)
            table.setHorizontalHeaderLabels(["状态", "时间(ms)", "模板", "阈值"])
            for row, state in enumerate(document.demonstration.states):
                table.setItem(row, 0, QTableWidgetItem(state.name))
                table.setItem(row, 1, QTableWidgetItem(str(state.timestamp_ms)))
                table.setItem(row, 2, QTableWidgetItem(state.template))
                table.setItem(row, 3, QTableWidgetItem(str(state.threshold)))
            approve = QPushButton("确认校准并导出 Maa 任务包")

            def export() -> None:
                try:
                    for row in range(table.rowCount()):
                        document.update_state(
                            row,
                            name=table.item(row, 0).text(),
                            threshold=float(table.item(row, 3).text()),
                        )
                    document.approve()
                    document.save(self.demo_path)
                    output = QFileDialog.getExistingDirectory(dialog, "选择任务包输出目录")
                    if output:
                        bundle = write_task_bundle(
                            document.demonstration, Path(output) / "simulator-task"
                        )
                        QMessageBox.information(dialog, "导出完成", str(bundle))
                except (ValueError, OSError) as exc:
                    QMessageBox.critical(dialog, "校准失败", str(exc))

            approve.clicked.connect(export)
            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.addWidget(table)
            content_layout.addWidget(approve)
            dialog.setCentralWidget(content)
            dialog.resize(900, 500)
            dialog.show()
            self.calibration_window = dialog

    app = QApplication(sys.argv)
    window = Studio()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
