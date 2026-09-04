from __future__ import annotations

from pathlib import Path
from typing import Any

from . import maa_runtime
from .models import WindowIdentity


def foreground_screencap_method(methods: Any) -> Any:
    """Use ScreenDC directly so each loop does not probe failing DXGI duplication."""
    return methods.ScreenDC


def foreground_input_method(methods: Any) -> Any:
    """Use Maa's highest-compatibility foreground input backend."""
    return methods.Seize


def require_maa_720p(controller: Any) -> None:
    if not controller.set_screenshot_use_raw_size(False):
        raise RuntimeError("MaaFramework 无法关闭原始截图，已安全暂停")
    if not controller.set_screenshot_target_short_side(720):
        raise RuntimeError("MaaFramework 无法设置短边 720，已安全暂停")


class Maa720pForegroundRunner(maa_runtime.MaaForegroundRunner):
    def run(self, bundle: str | Path, expected_window: WindowIdentity, entry: str = "entry") -> Any:
        from maa.controller import (
            MaaWin32InputMethodEnum,
            MaaWin32ScreencapMethodEnum,
            Win32Controller,
        )
        from maa.resource import Resource
        from maa.tasker import Tasker
        from maa.toolkit import Toolkit

        Toolkit.init_option(str(self.user_dir))
        selected = maa_runtime.select_exact_window(Toolkit.find_desktop_windows(), expected_window.title)
        live = maa_runtime.inspect_live_window(selected.hwnd)
        errors = maa_runtime.validate_live_window(expected_window, live)
        if errors:
            raise RuntimeError("；".join(errors))
        controller = Win32Controller(
            hWnd=selected.hwnd,
            screencap_method=foreground_screencap_method(MaaWin32ScreencapMethodEnum),
            mouse_method=foreground_input_method(MaaWin32InputMethodEnum),
            keyboard_method=foreground_input_method(MaaWin32InputMethodEnum),
        )
        require_maa_720p(controller)
        connection = controller.post_connection(); connection.wait()
        if not connection.succeeded:
            raise RuntimeError("MaaFramework 无法连接目标窗口")
        resource = Resource(); load_job = resource.post_bundle(str(Path(bundle).resolve())); load_job.wait()
        if not load_job.succeeded:
            raise RuntimeError("MaaFramework 任务资源加载失败")
        self.tasker = Tasker(); self.tasker.bind(resource, controller)
        if not self.tasker.inited:
            raise RuntimeError("MaaFramework Tasker 初始化失败")
        def stop() -> None:
            if self.tasker is not None:
                self.tasker.post_stop().wait()
        with maa_runtime.EmergencyStopHotkey(stop, 0x7B):
            job = self.tasker.post_task(entry); job.wait(); return job.get()
