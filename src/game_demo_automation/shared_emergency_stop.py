from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any


class SharedF12EmergencyStop:
    """Observe F12 without claiming the exclusive Windows global-hotkey slot."""

    def __init__(self, callback: Callable[[], None], virtual_key: int = 0x7B) -> None:
        if virtual_key != 0x7B:
            raise ValueError("shared emergency stop currently supports F12 only")
        self.callback = callback
        self.ready = threading.Event()
        self.failed: BaseException | None = None
        self._listener: Any = None
        self._triggered = threading.Event()

    def start(self) -> None:
        try:
            from pynput import keyboard

            def on_press(key: Any) -> None:
                if key == keyboard.Key.f12 and not self._triggered.is_set():
                    self._triggered.set()
                    self.callback()

            self._listener = keyboard.Listener(on_press=on_press)
            self._listener.start()
            if not self._listener.wait(timeout=3):
                raise RuntimeError("F12 键盘监听初始化超时")
            self.ready.set()
        except BaseException as exc:
            self.failed = exc
            self.ready.set()
            raise RuntimeError("无法启动非独占 F12 紧急停止监听") from exc

    def close(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener.join(timeout=2)
            self._listener = None

    def __enter__(self) -> SharedF12EmergencyStop:
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
