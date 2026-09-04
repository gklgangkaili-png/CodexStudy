from __future__ import annotations

import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from .calibration import CalibrationDocument
from .maa_runtime import MaaForegroundRunner
from .recording import RecordingSession
from .region_bundle import write_region_task_bundle
from .region_capture import (
    RegionTarget,
    ScreenRegion,
    build_region_draft,
    resolve_region_target,
)


def discover_task_bundles(root: str | Path) -> list[Path]:
    root = Path(root)
    if not root.exists():
        return []
    return sorted(
        [
            path.parent
            for path in root.rglob("task.json")
            if (path.parent / "pipeline" / "main.json").is_file()
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def main() -> None:
    try:
        from pynput import keyboard, mouse
        from PySide6.QtCore import QBuffer, QIODevice, QPoint, QRect, Qt, QThread, QTimer, Signal
        from PySide6.QtGui import (
            QColor,
            QGuiApplication,
            QKeySequence,
            QPainter,
            QPen,
            QPixmap,
            QShortcut,
        )
        from PySide6.QtWidgets import (
            QApplication,
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QFrame,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QTableWidget,
            QTableWidgetItem,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        raise SystemExit("缺少界面或录制依赖，请重新安装项目依赖") from exc

    class RegionSelector(QWidget):
        selected = Signal(object)
        cancelled = Signal()

        def __init__(self) -> None:
            super().__init__()
            geometry = QGuiApplication.primaryScreen().virtualGeometry()
            self.setGeometry(geometry)
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.start_point: QPoint | None = None
            self.end_point: QPoint | None = None
            self.showFullScreen()

        def mousePressEvent(self, event) -> None:
            if event.button() == Qt.MouseButton.LeftButton:
                self.start_point = event.position().toPoint()
                self.end_point = self.start_point
                self.update()

        def mouseMoveEvent(self, event) -> None:
            if self.start_point is not None:
                self.end_point = event.position().toPoint()
                self.update()

        def mouseReleaseEvent(self, event) -> None:
            if self.start_point is None or self.end_point is None:
                return
            local = QRect(self.start_point, self.end_point).normalized()
            if local.width() < 40 or local.height() < 40:
                QMessageBox.warning(self, "区域过小", "请至少框选 40×40 像素区域")
                return
            global_top_left = self.mapToGlobal(local.topLeft())
            self.hide()
            self.selected.emit(
                ScreenRegion(
                    global_top_left.x(), global_top_left.y(), local.width(), local.height()
                )
            )
            self.deleteLater()

        def keyPressEvent(self, event) -> None:
            if event.key() == Qt.Key.Key_Escape:
                self.cancelled.emit()
                self.close()

        def paintEvent(self, _event) -> None:
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 110))
            painter.setPen(QPen(QColor("#59a8ff"), 3))
            if self.start_point is not None and self.end_point is not None:
                rect = QRect(self.start_point, self.end_point).normalized()
                painter.fillRect(rect, QColor(70, 150, 255, 45))
                painter.drawRect(rect)
                painter.setPen(QColor("white"))
                painter.drawText(
                    rect.topLeft() + QPoint(8, -8), f"{rect.width()} × {rect.height()}"
                )
            painter.setPen(QColor("white"))
            painter.drawText(30, 45, "拖动鼠标选择录制区域，按 Esc 取消")

    class RecorderBridge(QWidget):
        stop_requested = Signal()

    class CalibrationDialog(QDialog):
        def __init__(self, demo_path: Path, parent=None) -> None:
            super().__init__(parent)
            self.demo_path = demo_path
            self.document = CalibrationDocument.load(demo_path)
            self.setWindowTitle("校准示教草稿")
            self.resize(960, 560)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("检查状态名称与匹配阈值。确认后才能导出 Maa 任务包。"))
            self.table = QTableWidget(len(self.document.demonstration.states), 4)
            self.table.setHorizontalHeaderLabels(["状态名称", "时间(ms)", "ROI", "阈值"])
            for row, state in enumerate(self.document.demonstration.states):
                for column, value in enumerate(
                    (
                        state.name,
                        str(state.timestamp_ms),
                        ",".join(map(str, state.roi)),
                        str(state.threshold),
                    )
                ):
                    self.table.setItem(row, column, QTableWidgetItem(value))
            layout.addWidget(self.table)
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.save)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)

        def save(self) -> None:
            try:
                for row in range(self.table.rowCount()):
                    self.document.update_state(
                        row,
                        name=self.table.item(row, 0).text().strip(),
                        threshold=float(self.table.item(row, 3).text()),
                    )
                self.document.approve()
                self.document.save(self.demo_path)
            except (ValueError, OSError) as exc:
                QMessageBox.critical(self, "校准失败", str(exc))
                return
            self.accept()

    class RunWorker(QThread):
        message = Signal(str)
        completed = Signal(str)
        failed = Signal(str)

        def __init__(self, bundle: Path, demo_path: Path) -> None:
            super().__init__()
            self.bundle = bundle
            self.demo_path = demo_path

        def run(self) -> None:
            try:
                demo = CalibrationDocument.load(self.demo_path).demonstration
                for remaining in range(3, 0, -1):
                    self.message.emit(f"{remaining} 秒后启动 Maa，请切换到目标窗口")
                    time.sleep(1)
                result = MaaForegroundRunner(self.bundle / "maa-user").run(self.bundle, demo.window)
                self.completed.emit(str(result))
            except BaseException:
                self.failed.emit(traceback.format_exc())

    class WorkflowWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Game Demo Automation")
            self.resize(1040, 720)
            self.recordings_root = Path.cwd() / "recordings"
            self.tasks_root = Path.cwd() / "tasks"
            self.tasks_root.mkdir(exist_ok=True)
            self.session: RecordingSession | None = None
            self.target: RegionTarget | None = None
            self.frame_timer = QTimer(self)
            self.frame_timer.setInterval(1000 // 15)
            self.frame_timer.timeout.connect(self.capture_frame)
            self.keyboard_listener = None
            self.mouse_listener = None
            self.latest_demo: Path | None = None
            self.worker: RunWorker | None = None
            self.bridge = RecorderBridge()
            self.bridge.stop_requested.connect(self.stop_recording)
            root = QWidget()
            layout = QVBoxLayout(root)
            title = QLabel("Game Demo Automation")
            title.setStyleSheet("font-size: 30px; font-weight: 700")
            subtitle = QLabel("录制一次操作，校准关键状态，导出并执行 Maa 任务")
            subtitle.setStyleSheet("color: #667085; font-size: 15px")
            layout.addWidget(title)
            layout.addWidget(subtitle)
            layout.addSpacing(12)

            self.record_button = self.add_step(
                layout,
                "1",
                "开始录制示教视频",
                "点击后拖动选择录制区域。录制期间按 F10 停止。",
                "选择区域并开始录制",
                self.start_region_selection,
            )
            self.calibrate_button = self.add_step(
                layout,
                "2",
                "校准并导出成 Maa 任务包",
                "检查自动提取的关键状态，确认阈值并保存到任务包库。",
                "校准并导出",
                self.calibrate_and_export,
            )
            self.task_combo = QComboBox()
            self.task_combo.setMinimumWidth(420)
            self.task_combo.currentIndexChanged.connect(self.update_execute_state)
            self.add_task_selector(layout)
            self.execute_button = self.add_step(
                layout,
                "4",
                "启动 Maa 执行",
                "执行前有 3 秒倒计时；必须保持目标窗口前台，F12 紧急停止。",
                "启动 Maa",
                self.execute_selected,
            )
            self.calibrate_button.setEnabled(False)
            self.execute_button.setEnabled(False)
            layout.addWidget(QLabel("运行日志"))
            self.log = QTextEdit()
            self.log.setReadOnly(True)
            self.log.setMaximumHeight(150)
            layout.addWidget(self.log)
            self.setCentralWidget(root)
            QShortcut(QKeySequence("F10"), self, activated=self.stop_recording)
            self.refresh_tasks()

        def add_step(self, layout, number, heading, description, button_text, callback):
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            row = QHBoxLayout(frame)
            badge = QLabel(number)
            badge.setFixedSize(40, 40)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                "background:#1677ff;color:white;border-radius:20px;font-size:18px;font-weight:bold"
            )
            texts = QVBoxLayout()
            name = QLabel(heading)
            name.setStyleSheet("font-size:18px;font-weight:600")
            detail = QLabel(description)
            detail.setStyleSheet("color:#667085")
            detail.setWordWrap(True)
            texts.addWidget(name)
            texts.addWidget(detail)
            button = QPushButton(button_text)
            button.setMinimumWidth(180)
            button.setMinimumHeight(40)
            button.clicked.connect(callback)
            row.addWidget(badge)
            row.addLayout(texts, 1)
            row.addWidget(button)
            layout.addWidget(frame)
            return button

        def add_task_selector(self, layout) -> None:
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            row = QHBoxLayout(frame)
            badge = QLabel("3")
            badge.setFixedSize(40, 40)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                "background:#1677ff;color:white;border-radius:20px;font-size:18px;font-weight:bold"
            )
            texts = QVBoxLayout()
            name = QLabel("选择 Maa 任务包")
            name.setStyleSheet("font-size:18px;font-weight:600")
            texts.addWidget(name)
            texts.addWidget(QLabel("任务包库中的所有已导出任务。"))
            tools = QHBoxLayout()
            tools.addWidget(self.task_combo)
            refresh = QPushButton("刷新")
            refresh.clicked.connect(self.refresh_tasks)
            tools.addWidget(refresh)
            row.addWidget(badge)
            row.addLayout(texts, 1)
            row.addLayout(tools)
            layout.addWidget(frame)

        def append_log(self, text: str) -> None:
            self.log.append(text)
            self.statusBar().showMessage(text.splitlines()[0])

        def start_region_selection(self) -> None:
            if self.session is not None:
                self.stop_recording()
                return
            self.hide()
            QTimer.singleShot(250, self.show_selector)

        def show_selector(self) -> None:
            self.selector = RegionSelector()
            self.selector.selected.connect(self.region_selected)
            self.selector.cancelled.connect(self.show)

        def region_selected(self, region: ScreenRegion) -> None:
            try:
                self.target = resolve_region_target(region)
            except (ValueError, RuntimeError, OSError) as exc:
                self.show()
                QMessageBox.critical(self, "区域无效", str(exc))
                return
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            root = self.recordings_root / stamp
            self.session = RecordingSession(root, self.target.window, fps=15)
            self.start_input_listeners()
            self.frame_timer.start()
            self.record_button.setText("停止录制（F10）")
            self.showMinimized()
            self.append_log(
                f"正在录制 {region.width}×{region.height} 区域，目标窗口：{self.target.window.title}"
            )

        def start_input_listeners(self) -> None:
            def on_click(x, y, _button, pressed):
                if not pressed or self.session is None or self.target is None:
                    return
                if self.target.screen_region.contains(x, y):
                    client_x, client_y = self.target.screen_to_client(x, y)
                    self.session.record_event("mouse_click", x=client_x, y=client_y)

            def on_move(x, y):
                if self.session is None or self.target is None:
                    return
                if self.target.screen_region.contains(x, y):
                    client_x, client_y = self.target.screen_to_client(x, y)
                    try:
                        self.session.record_event("mouse_move", x=client_x, y=client_y)
                    except ValueError:
                        pass

            def key_code(key):
                return getattr(key, "vk", None)

            def on_press(key):
                if key == keyboard.Key.f10:
                    self.bridge.stop_requested.emit()
                    return
                if self.session is not None:
                    code = key_code(key)
                    if code is not None:
                        try:
                            self.session.record_event("key_down", key=code)
                        except ValueError:
                            pass

            def on_release(key):
                if self.session is not None and key != keyboard.Key.f10:
                    code = key_code(key)
                    if code is not None:
                        try:
                            self.session.record_event("key_up", key=code)
                        except ValueError:
                            pass

            self.mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)
            self.keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self.mouse_listener.start()
            self.keyboard_listener.start()

        def capture_frame(self) -> None:
            if self.session is None or self.target is None:
                return
            region = self.target.screen_region
            screen = QGuiApplication.screenAt(
                QPoint(region.x + region.width // 2, region.y + region.height // 2)
            )
            if screen is None:
                return
            geometry = screen.geometry()
            pixmap = screen.grabWindow(
                0,
                region.x - geometry.x(),
                region.y - geometry.y(),
                region.width,
                region.height,
            )
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, "PNG")
            self.session.record_frame(bytes(buffer.data()))

        def stop_recording(self) -> None:
            if self.session is None or self.target is None:
                return
            self.frame_timer.stop()
            for listener in (self.mouse_listener, self.keyboard_listener):
                if listener is not None:
                    listener.stop()
            try:
                demo = build_region_draft(
                    self.session, self.target, f"task-{self.session.root.name}"
                )
                self.latest_demo = self.session.root / "demonstration.json"
                self.append_log(
                    f"录制完成：{len(demo.events)} 个输入，{len(demo.states)} 个候选状态"
                )
                self.calibrate_button.setEnabled(True)
            except (ValueError, OSError) as exc:
                QMessageBox.critical(self, "生成草稿失败", str(exc))
            finally:
                self.session.close()
                self.session = None
                self.target = None
                self.record_button.setText("选择区域并开始录制")
                self.showNormal()
                self.activateWindow()

        def calibrate_and_export(self) -> None:
            if self.latest_demo is None:
                return
            dialog = CalibrationDialog(self.latest_demo, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            demo = dialog.document.demonstration
            safe_name = "".join(
                character if character.isalnum() or character in "-_" else "_"
                for character in demo.name
            )
            destination = self.tasks_root / safe_name
            try:
                write_region_task_bundle(demo, destination)
            except (ValueError, OSError) as exc:
                QMessageBox.critical(self, "导出失败", str(exc))
                return
            self.append_log(f"任务包已导出：{destination}")
            self.refresh_tasks()

        def refresh_tasks(self) -> None:
            self.bundles = discover_task_bundles(self.tasks_root)
            self.task_combo.clear()
            for bundle in self.bundles:
                self.task_combo.addItem(bundle.name, str(bundle))
            self.update_execute_state()

        def update_execute_state(self) -> None:
            self.execute_button.setEnabled(bool(self.bundles) and self.worker is None)

        def execute_selected(self) -> None:
            index = self.task_combo.currentIndex()
            if index < 0 or index >= len(self.bundles):
                return
            bundle = self.bundles[index]
            worker = RunWorker(bundle, bundle / "demonstration.json")
            worker.message.connect(self.append_log)
            worker.completed.connect(self.execution_completed)
            worker.failed.connect(self.execution_failed)
            worker.finished.connect(self.execution_worker_finished)
            self.worker = worker
            self.execute_button.setEnabled(False)
            worker.start()

        def execution_completed(self, detail: str) -> None:
            self.append_log(f"Maa 执行结束：{detail}")

        def execution_failed(self, detail: str) -> None:
            self.append_log(detail)
            QMessageBox.critical(self, "Maa 执行失败", detail.splitlines()[-1])

        def execution_worker_finished(self) -> None:
            worker = self.worker
            self.worker = None
            if worker is not None:
                worker.deleteLater()
            self.update_execute_state()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = WorkflowWindow()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
