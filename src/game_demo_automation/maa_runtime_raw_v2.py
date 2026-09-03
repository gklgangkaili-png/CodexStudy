from __future__ import annotations

from pathlib import Path
from typing import Any

from . import maa_runtime
from .models import WindowIdentity


def require_raw_screenshot(controller: Any) -> None:
    """Keep Maa recognition and recorded Win32 client coordinates in one space."""
    if not controller.set_screenshot_use_raw_size(True):
        raise RuntimeError("MaaFramework 无法启用原始截图尺寸，已安全暂停")


class MaaRawForegroundRunner(maa_runtime.MaaForegroundRunner):
    """Maa runner whose screenshot size matches the recorded client coordinates."""

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
        selected = maa_runtime.select_exact_window(
            Toolkit.find_desktop_windows(), expected_window.title
        )
        live = maa_runtime.inspect_live_window(selected.hwnd)
        errors = maa_runtime.validate_live_window(expected_window, live)
        if errors:
            raise RuntimeError("；".join(errors))

        controller = Win32Controller(
            hWnd=selected.hwnd,
            screencap_method=MaaWin32ScreencapMethodEnum.Foreground,
            mouse_method=MaaWin32InputMethodEnum.Seize,
            keyboard_method=MaaWin32InputMethodEnum.Seize,
        )
        require_raw_screenshot(controller)
        connection = controller.post_connection()
        connection.wait()
        if not connection.succeeded:
            raise RuntimeError("MaaFramework 无法连接目标窗口")

        capture = controller.post_screencap()
        capture.wait()
        if not capture.succeeded:
            raise RuntimeError("MaaFramework 无法获取原始尺寸截图")
        image = controller.cached_image
        actual_height, actual_width = image.shape[:2]
        if (actual_width, actual_height) != (
            expected_window.client_width,
            expected_window.client_height,
        ):
            raise RuntimeError(
                "Maa 原始截图尺寸与示教窗口不一致："
                f"当前 {actual_width}×{actual_height}，"
                f"示教 {expected_window.client_width}×{expected_window.client_height}；"
                "请保持相同分辨率后重试"
            )

        resource = Resource()
        load_job = resource.post_bundle(str(Path(bundle).resolve()))
        load_job.wait()
        if not load_job.succeeded:
            raise RuntimeError("MaaFramework 任务资源加载失败")

        self.tasker = Tasker()
        self.tasker.bind(resource, controller)
        if not self.tasker.inited:
            raise RuntimeError("MaaFramework Tasker 初始化失败")

        def stop() -> None:
            if self.tasker is not None:
                self.tasker.post_stop().wait()

        with maa_runtime.EmergencyStopHotkey(stop, 0x7B):
            job = self.tasker.post_task(entry)
            job.wait()
            return job.get()
