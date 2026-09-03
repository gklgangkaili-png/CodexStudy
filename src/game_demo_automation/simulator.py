import random
import sys


def main() -> None:
    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import (
            QApplication,
            QHBoxLayout,
            QLabel,
            QMainWindow,
            QPushButton,
            QSpinBox,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        raise SystemExit("Install UI dependencies with: pip install -e '.[ui]'") from exc

    class Simulator(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Game Demo Simulator")
            self.setFixedSize(960, 540)
            self.runs = 0
            root, layout = QWidget(), QVBoxLayout()
            root.setLayout(layout)
            self.title, self.status, self.action = QLabel(), QLabel(), QPushButton()
            self.title.setStyleSheet("font-size: 32px; font-weight: bold")
            self.status.setStyleSheet("font-size: 20px")
            self.action.setMinimumHeight(72)
            self.action.clicked.connect(self.advance)
            options = QHBoxLayout()
            options.addWidget(QLabel("目标循环次数"))
            self.loops = QSpinBox()
            self.loops.setRange(1, 20)
            self.loops.setValue(3)
            options.addWidget(self.loops)
            failure = QPushButton("注入未示教失败")
            failure.clicked.connect(lambda: self.show_state("failure"))
            options.addWidget(failure)
            layout.addWidget(self.title)
            layout.addWidget(self.status)
            layout.addStretch()
            layout.addWidget(self.action)
            layout.addLayout(options)
            self.setCentralWidget(root)
            self.show_state("select")

        def show_state(self, state: str) -> None:
            labels = {
                "select": ("STATE: SELECT_LEVEL", "选择固定副本", "开始挑战"),
                "loading": ("STATE: LOADING", "随机加载中……", "请等待"),
                "battle": ("STATE: BATTLE", "按住 W 模拟固定路线移动", "完成本轮"),
                "result": ("STATE: RESULT", f"已完成 {self.runs} 次", "再次挑战"),
                "done": ("STATE: DONE", "任务已达到最大循环次数", "重置"),
                "failure": ("STATE: UNKNOWN_FAILURE", "这是未示教状态，应触发安全暂停", "返回选关"),
            }
            self.state = state
            title, status, action = labels[state]
            self.title.setText(title)
            self.status.setText(status)
            self.action.setText(action)
            self.action.setEnabled(state != "loading")

        def advance(self) -> None:
            if self.state == "select":
                self.show_state("loading")
                QTimer.singleShot(random.randint(600, 1800), lambda: self.show_state("battle"))
            elif self.state == "battle":
                self.runs += 1
                self.show_state("result")
            elif self.state == "result":
                if self.runs >= self.loops.value():
                    self.show_state("done")
                else:
                    self.show_state("loading")
                    QTimer.singleShot(random.randint(600, 1800), lambda: self.show_state("battle"))
            elif self.state in {"done", "failure"}:
                self.runs = 0
                self.show_state("select")

    app = QApplication(sys.argv)
    window = Simulator()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
