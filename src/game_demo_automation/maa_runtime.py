from __future__ import annotations

import os
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Self

from .models import WindowIdentity


class WindowInfo(Protocol):
    hwnd: int
    window_name: str


@dataclass(frozen=True)
class LiveWindow:
    hwnd: int
    title: str
    executable: str
    client_width: int
    client_height: int
    is_foreground: bool


def select_exact_window(windows: Iterable[WindowInfo], title: str) -> WindowInfo:
    matches = [window for window in windows if window.window_name == title]
    if not matches:
        raise RuntimeError(f"找不到标题完全匹配的目标窗口：{title}")
    if len(matches) > 1:
        raise RuntimeError(f"存在 {len(matches)} 个同名窗口，拒绝选择不明确的目标")
    return matches[0]


def inspect_live_window(hwnd: int) -> LiveWindow:
    if os.name != "nt":
        raise RuntimeError("Maa Win32 runner only supports Windows")
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    title_length = user32.GetWindowTextLengthW(hwnd)
    title_buffer = ctypes.create_unicode_buffer(title_length + 1)
    user32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))

    rect = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise OSError(ctypes.get_last_error(), "GetClientRect failed")

    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    process = kernel32.OpenProcess(0x1000, False, process_id.value)
    if not process:
        raise OSError(ctypes.get_last_error(), "OpenProcess failed")
    try:
        capacity = wintypes.DWORD(32768)
        path_buffer = ctypes.create_unicode_buffer(capacity.value)
        if not kernel32.QueryFullProcessImageNameW(process, 0, path_buffer, ctypes.byref(capacity)):
            raise OSError(ctypes.get_last_error(), "QueryFullProcessImageNameW failed")
        executable = Path(path_buffer.value).name
    finally:
        kernel32.CloseHandle(process)

    return LiveWindow(
        hwnd=hwnd,
        title=title_buffer.value,
        executable=executable,
        client_width=rect.right - rect.left,
        client_height=rect.bottom - rect.top,
        is_foreground=user32.GetForegroundWindow() == hwnd,
    )


def validate_live_window(expected: WindowIdentity, live: LiveWindow) -> list[str]:
    errors: list[str] = []
    if live.title != expected.title:
        errors.append("窗口标题不匹配")
    if live.executable.casefold() != Path(expected.executable).name.casefold():
        errors.append("窗口进程不匹配")
    if (live.client_width, live.client_height) != (
        expected.client_width,
        expected.client_height,
    ):
        errors.append("客户区分辨率不匹配")
    if not live.is_foreground:
        errors.append("目标窗口不在前台")
    return errors


class EmergencyStopHotkey:
    """Register F12 globally and call Maa Tasker.post_stop on activation."""

    def __init__(self, callback: Callable[[], None], virtual_key: int = 0x7B) -> None:
        self.callback = callback
        self.virtual_key = virtual_key
        self.ready = threading.Event()
        self.failed: BaseException | None = None
        self._thread_id = 0
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if os.name != "nt":
            raise RuntimeError("global emergency hotkey only supports Windows")
        self._thread = threading.Thread(target=self._run, name="emergency-stop", daemon=True)
        self._thread.start()
        if not self.ready.wait(timeout=3):
            raise RuntimeError("紧急停止热键初始化超时")
        if self.failed is not None:
            raise RuntimeError("无法注册 F12 紧急停止热键") from self.failed

    def _run(self) -> None:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._thread_id = kernel32.GetCurrentThreadId()
        hotkey_id = 0x4D41
        if not user32.RegisterHotKey(None, hotkey_id, 0, self.virtual_key):
            self.failed = OSError(ctypes.get_last_error(), "RegisterHotKey failed")
            self.ready.set()
            return
        self.ready.set()
        message = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == 0x0312 and message.wParam == hotkey_id:
                    self.callback()
        finally:
            user32.UnregisterHotKey(None, hotkey_id)

    def close(self) -> None:
        if self._thread_id:
            import ctypes

            ctypes.WinDLL("user32", use_last_error=True).PostThreadMessageW(
                self._thread_id, 0x0012, 0, 0
            )
        if self._thread is not None:
            self._thread.join(timeout=2)

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class MaaForegroundRunner:
    def __init__(self, user_dir: str | Path) -> None:
        self.user_dir = Path(user_dir)
        self.tasker: Any = None

    def run(
        self,
        bundle: str | Path,
        expected_window: WindowIdentity,
        entry: str = "entry",
    ) -> Any:
        from maa.controller import (
            MaaWin32InputMethodEnum,
            MaaWin32ScreencapMethodEnum,
            Win32Controller,
        )
        from maa.resource import Resource
        from maa.tasker import Tasker
        from maa.toolkit import Toolkit

        Toolkit.init_option(str(self.user_dir))
        selected = select_exact_window(Toolkit.find_desktop_windows(), expected_window.title)
        live = inspect_live_window(selected.hwnd)
        errors = validate_live_window(expected_window, live)
        if errors:
            raise RuntimeError("；".join(errors))

        resource = Resource()
        load_job = resource.post_bundle(str(Path(bundle).resolve()))
        load_job.wait()
        if not load_job.succeeded:
            raise RuntimeError("MaaFramework 任务资源加载失败")

        controller = Win32Controller(
            hWnd=selected.hwnd,
            screencap_method=MaaWin32ScreencapMethodEnum.Foreground,
            mouse_method=MaaWin32InputMethodEnum.Seize,
            keyboard_method=MaaWin32InputMethodEnum.Seize,
        )
        connection = controller.post_connection()
        connection.wait()
        if not connection.succeeded:
            raise RuntimeError("MaaFramework 无法连接目标窗口")

        self.tasker = Tasker()
        self.tasker.bind(resource, controller)
        if not self.tasker.inited:
            raise RuntimeError("MaaFramework Tasker 初始化失败")

        def stop() -> None:
            if self.tasker is not None:
                self.tasker.post_stop().wait()

        with EmergencyStopHotkey(stop, expected_window and 0x7B):
            job = self.tasker.post_task(entry)
            job.wait()
            return job.get()
