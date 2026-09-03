from __future__ import annotations

import ctypes
import sys
import time
import traceback
from pathlib import Path

from .calibration import CalibrationDocument
from .maa_runtime import MaaForegroundRunner, select_exact_window
from .models import Demonstration
from .portable_bundle import write_portable_task_bundle


def discover_recordings(root: str | Path) -> list[Path]:
    root = Path(root)
    if not root.exists():
        return []
    candidates: list[tuple[float, Path]] = []
    for path in root.rglob("demonstration.json"):
        try:
            Demonstration.load(path).validate()
        except (OSError, ValueError, KeyError):
            continue
        candidates.append((path.stat().st_mtime, path))
    return [path for _, path in sorted(candidates, reverse=True)]


def focus_window(title: str, user_dir: Path) -> None:
    from maa.toolkit import Toolkit

    Toolkit.init_option(str(user_dir))
    window = select_exact_window(Toolkit.find_desktop_windows(), title)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.ShowWindow(window.hwnd, 9)
    if not user32.SetForegroundWindow(window.hwnd):
        raise RuntimeError("无法把模拟窗口切换到前台")


def main() -> None:
    try:
        from PySide6.QtCore import QProcess, QThread, Signal
        from PySide6.QtWidgets import (
            QApplication,
            QFileDialog,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QSplitter,
            QTableWidget,
            QTableWidgetItem,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        raise SystemExit("请先安装界面依赖：py -m pip install --user -e '.[ui,maa]'") from exc

    class ReplayWorker(QThread):
        progress = Signal(str)
        succeeded = Signal(str)
        failed = Signal(str)

        def __init__(self, demo: Demonstration, bundle: Path) -> None:
            super().__init__()
            self.demo = demo
            self.bundle = bundle

        def run(self) -> None:
            try:
                for remaining in range(3, 0, -1):
                    self.progress.emit(f"{remaining} 秒后开始回放……")
                    time.sleep(1)
                user_dir = self.bundle.parent / "maa-user"
                focus_window(self.demo.window.title, user_dir)
                self.progress.emit("正在运行；按 F12 可紧急停止")
                result = MaaForegroundRunner(user_dir).run(self.bundle, self.demo.window)
                self.succeeded.emit(str(result))
            except BaseException:
                self.failed.emit(traceback.format_exc())

    class ControlCenter(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Game Demo Automation 控制中心")
            self.resize(1180, 760)
            self.recordings_root = Path.cwd() / "recordings"
            self.current_path: Path | None = None
            self.current_document: CalibrationDocument | None = None
            self.studio_process: QProcess | None = None
            self.replay_worker: ReplayWorker | None = None

            root = QWidget()
            root_layout = QVBoxLayout(root)
            toolbar = QHBoxLayout()
            launch = QPushButton("1. 启动示教模拟器")
            launch.clicked.connect(self.launch_studio)
            choose = QPushButton("选择录制目录")
            choose.clicked.connect(self.choose_root)
            refresh = QPushButton("刷新录制")
            refresh.clicked.connect(self.refresh_recordings)
            toolbar.addWidget(launch)
            toolbar.addWidget(choose)
            toolbar.addWidget(refresh)
            toolbar.addStretch()
            self.root_label = QLabel(str(self.recordings_root))
            toolbar.addWidget(self.root_label)
            root_layout.addLayout(toolbar)

            splitter = QSplitter()
            left = QWidget()
            left_layout = QVBoxLayout(left)
            left_layout.addWidget(QLabel("完整示教"))
            self.recording_list = QListWidget()
            self.recording_list.currentRowChanged.connect(self.select_recording)
            left_layout.addWidget(self.recording_list)
            splitter.addWidget(left)

            right = QWidget()
            right_layout = QVBoxLayout(right)
            self.summary = QLabel("选择一条录制以查看详情")
            self.summary.setWordWrap(True)
            right_layout.addWidget(self.summary)
            self.state_table = QTableWidget(0, 5)
            self.state_table.setHorizontalHeaderLabels(
                ["状态名称", "时间(ms)", "ROI", "模板", "阈值"]
            )
            self.state_table.horizontalHeader().setStretchLastSection(True)
            right_layout.addWidget(self.state_table)
            actions = QHBoxLayout()
            self.save_button = QPushButton("2. 保存并确认校准")
            self.save_button.clicked.connect(self.save_calibration)
            self.export_button = QPushButton("3. 导出 Maa 任务包")
            self.export_button.clicked.connect(self.export_bundle)
            self.replay_button = QPushButton("4. 回放选中任务")
            self.replay_button.clicked.connect(self.replay)
            for button in (self.save_button, self.export_button, self.replay_button):
                button.setEnabled(False)
                actions.addWidget(button)
            right_layout.addLayout(actions)
            right_layout.addWidget(QLabel("运行日志"))
            self.log = QTextEdit()
            self.log.setReadOnly(True)
            right_layout.addWidget(self.log)
            splitter.addWidget(right)
            splitter.setSizes([330, 850])
            root_layout.addWidget(splitter)
            self.setCentralWidget(root)
            self.statusBar().showMessage("先启动模拟器并完成一次录制")
            self.refresh_recordings()

        def append_log(self, message: str) -> None:
            self.log.append(message)
            self.statusBar().showMessage(message.splitlines()[0])

        def launch_studio(self) -> None:
            if (
                self.studio_process is not None
                and self.studio_process.state() != QProcess.ProcessState.NotRunning
            ):
                self.append_log("示教模拟器已经在运行")
                return
            process = QProcess(self)
            process.setWorkingDirectory(str(Path.cwd()))
            process.setProgram(sys.executable)
            process.setArguments(["-m", "game_demo_automation.studio"])
            process.errorOccurred.connect(lambda error: self.append_log(f"模拟器启动失败：{error}"))
            process.finished.connect(
                lambda code, _status: self.append_log(f"模拟器已退出，代码 {code}")
            )
            process.start()
            if not process.waitForStarted(5000):
                QMessageBox.critical(self, "启动失败", process.errorString())
                return
            self.studio_process = process
            self.append_log("示教模拟器已启动；请在其中完成录制并停止录制")

        def choose_root(self) -> None:
            selected = QFileDialog.getExistingDirectory(
                self, "选择包含示教的目录", str(self.recordings_root)
            )
            if selected:
                self.recordings_root = Path(selected)
                self.root_label.setText(selected)
                self.refresh_recordings()

        def refresh_recordings(self) -> None:
            self.paths = discover_recordings(self.recordings_root)
            self.recording_list.clear()
            for path in self.paths:
                try:
                    demo = Demonstration.load(path)
                    flag = "✓ 已校准" if demo.calibrated else "○ 待校准"
                    label = f"{flag}  {path.parent.name}  ·  {len(demo.states)} 状态"
                except (OSError, ValueError, KeyError):
                    label = f"! 无效  {path}"
                self.recording_list.addItem(label)
            self.append_log(f"发现 {len(self.paths)} 条有效完整示教")

        def select_recording(self, row: int) -> None:
            if row < 0 or row >= len(self.paths):
                return
            self.current_path = self.paths[row]
            try:
                self.current_document = CalibrationDocument.load(self.current_path)
                demo = self.current_document.demonstration
                demo.validate()
            except (OSError, ValueError, KeyError) as exc:
                QMessageBox.critical(self, "读取失败", str(exc))
                return
            self.summary.setText(
                f"任务：{demo.name}\n窗口：{demo.window.title} / {demo.window.executable} / "
                f"{demo.window.client_width}×{demo.window.client_height}\n"
                f"输入事件：{len(demo.events)}，FPS：{demo.fps}，"
                f"状态：{'已校准' if demo.calibrated else '待校准'}"
            )
            self.state_table.setRowCount(len(demo.states))
            for row_index, state in enumerate(demo.states):
                values = (
                    state.name,
                    str(state.timestamp_ms),
                    ",".join(map(str, state.roi)),
                    state.template,
                    str(state.threshold),
                )
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if column in {1, 2, 3}:
                        item.setFlags(item.flags() & ~item.flags().ItemIsEditable)
                    self.state_table.setItem(row_index, column, item)
            self.save_button.setEnabled(True)
            self.export_button.setEnabled(demo.calibrated)
            self.replay_button.setEnabled(demo.calibrated)
            self.append_log(f"已加载 {self.current_path}")

        def save_calibration(self) -> None:
            if self.current_document is None or self.current_path is None:
                return
            try:
                for row in range(self.state_table.rowCount()):
                    self.current_document.update_state(
                        row,
                        name=self.state_table.item(row, 0).text().strip(),
                        threshold=float(self.state_table.item(row, 4).text()),
                    )
                self.current_document.approve()
                self.current_document.save(self.current_path)
            except (ValueError, OSError) as exc:
                QMessageBox.critical(self, "校准失败", str(exc))
                return
            self.export_button.setEnabled(True)
            self.replay_button.setEnabled(True)
            self.append_log("校准已保存并确认")
            self.refresh_recordings()

        def export_bundle(self) -> None:
            if self.current_document is None:
                return
            selected = QFileDialog.getExistingDirectory(
                self, "选择任务包输出目录", str(self.current_path.parent)
            )
            if not selected:
                return
            try:
                bundle = write_portable_task_bundle(
                    self.current_document.demonstration,
                    Path(selected) / "maa-bundle",
                )
            except (ValueError, OSError, RuntimeError) as exc:
                QMessageBox.critical(self, "导出失败", str(exc))
                return
            self.append_log(f"Maa 任务包已导出：{bundle}")

        def replay(self) -> None:
            if self.current_document is None or self.current_path is None:
                return
            if self.replay_worker is not None and self.replay_worker.isRunning():
                QMessageBox.information(self, "正在运行", "当前已有回放任务")
                return
            try:
                bundle = write_portable_task_bundle(
                    self.current_document.demonstration,
                    self.current_path.parent / "maa-bundle",
                )
            except (ValueError, OSError, RuntimeError) as exc:
                QMessageBox.critical(self, "准备失败", str(exc))
                return
            worker = ReplayWorker(self.current_document.demonstration, bundle)
            worker.progress.connect(self.append_log)
            worker.succeeded.connect(lambda result: self.replay_finished(True, result))
            worker.failed.connect(lambda error: self.replay_finished(False, error))
            self.replay_worker = worker
            self.replay_button.setEnabled(False)
            self.append_log("正在准备回放，请不要操作其他窗口")
            worker.start()

        def replay_finished(self, succeeded: bool, detail: str) -> None:
            self.replay_button.setEnabled(True)
            if succeeded:
                self.append_log(f"回放结束：{detail}")
                QMessageBox.information(self, "回放结束", "任务已经结束")
            else:
                self.append_log(detail)
                QMessageBox.critical(self, "回放失败", detail.splitlines()[-1])

    app = QApplication(sys.argv)
    window = ControlCenter()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
