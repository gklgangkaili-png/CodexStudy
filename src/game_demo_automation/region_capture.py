from __future__ import annotations

import json
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import Demonstration, InputEvent, StateMarker, WindowIdentity
from .recording import RecordingSession


@dataclass(frozen=True)
class ScreenRegion:
    x: int
    y: int
    width: int
    height: int

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height


@dataclass(frozen=True)
class RegionTarget:
    hwnd: int
    window: WindowIdentity
    client_origin_x: int
    client_origin_y: int
    screen_region: ScreenRegion

    @property
    def client_roi(self) -> tuple[int, int, int, int]:
        return (
            self.screen_region.x - self.client_origin_x,
            self.screen_region.y - self.client_origin_y,
            self.screen_region.width,
            self.screen_region.height,
        )

    def screen_to_client(self, x: int, y: int) -> tuple[int, int]:
        return x - self.client_origin_x, y - self.client_origin_y


def resolve_region_target(region: ScreenRegion) -> RegionTarget:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    center = wintypes.POINT(region.x + region.width // 2, region.y + region.height // 2)
    hwnd = user32.GetAncestor(user32.WindowFromPoint(center), 2)
    if not hwnd:
        raise RuntimeError("框选区域下方没有可控制的窗口")
    title_length = user32.GetWindowTextLengthW(hwnd)
    title_buffer = ctypes.create_unicode_buffer(title_length + 1)
    user32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))
    if not title_buffer.value.strip():
        raise RuntimeError("目标窗口没有可识别标题")

    client_rect = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(client_rect)):
        raise OSError(ctypes.get_last_error(), "GetClientRect failed")
    origin = wintypes.POINT(0, 0)
    if not user32.ClientToScreen(hwnd, ctypes.byref(origin)):
        raise OSError(ctypes.get_last_error(), "ClientToScreen failed")
    client_width = client_rect.right - client_rect.left
    client_height = client_rect.bottom - client_rect.top
    if (
        region.x < origin.x
        or region.y < origin.y
        or region.x + region.width > origin.x + client_width
        or region.y + region.height > origin.y + client_height
    ):
        raise ValueError("录制区域必须完全位于同一个窗口的客户区内")

    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    process = kernel32.OpenProcess(0x1000, False, process_id.value)
    if not process:
        raise OSError(ctypes.get_last_error(), "OpenProcess failed")
    try:
        capacity = wintypes.DWORD(32768)
        executable_buffer = ctypes.create_unicode_buffer(capacity.value)
        if not kernel32.QueryFullProcessImageNameW(
            process, 0, executable_buffer, ctypes.byref(capacity)
        ):
            raise OSError(ctypes.get_last_error(), "QueryFullProcessImageNameW failed")
        executable = Path(executable_buffer.value).name
    finally:
        kernel32.CloseHandle(process)

    return RegionTarget(
        hwnd=hwnd,
        window=WindowIdentity(title_buffer.value, executable, client_width, client_height),
        client_origin_x=origin.x,
        client_origin_y=origin.y,
        screen_region=region,
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError:
            break
    return result


def derive_state_times(
    events: Iterable[InputEvent], frame_times: list[int], minimum_gap_ms: int = 350
) -> list[int]:
    if not frame_times:
        raise ValueError("录制没有产生任何画面帧")
    candidates = [frame_times[0]]
    for event in events:
        if event.kind not in {"mouse_click", "key_down"}:
            continue
        prior_frames = [timestamp for timestamp in frame_times if timestamp <= event.timestamp_ms]
        timestamp = prior_frames[-1] if prior_frames else frame_times[0]
        if timestamp - candidates[-1] >= minimum_gap_ms:
            candidates.append(timestamp)
    if frame_times[-1] - candidates[-1] >= minimum_gap_ms:
        candidates.append(frame_times[-1])
    if len(candidates) == 1:
        candidates.append(frame_times[-1])
    return candidates


def build_region_draft(session: RecordingSession, target: RegionTarget, name: str) -> Demonstration:
    event_records = _read_jsonl(session.events_path)
    frame_records = _read_jsonl(session.frames_path)
    events = [InputEvent(**record) for record in event_records]
    frame_times = [int(record["timestamp_ms"]) for record in frame_records]
    state_times = derive_state_times(events, frame_times)
    states: list[StateMarker] = []
    for index, timestamp in enumerate(state_times):
        eligible = [record for record in frame_records if int(record["timestamp_ms"]) <= timestamp]
        record = eligible[-1] if eligible else frame_records[0]
        source = session.root / record["file"]
        template = session.templates_dir / f"state_{index:03d}.png"
        shutil.copy2(source, template)
        states.append(
            StateMarker(
                timestamp_ms=timestamp,
                name=f"state_{index + 1}",
                template=str(template),
                roi=target.client_roi,
            )
        )
    demo = Demonstration(
        name=name,
        window=target.window,
        events=events,
        states=states,
        calibrated=False,
        fps=session.fps,
        video_path=str(session.frames_dir),
    )
    demo.validate()
    demo.save(session.root / "demonstration.json")
    (session.root / "region.json").write_text(
        json.dumps(
            {
                "hwnd_at_recording": target.hwnd,
                "screen_region": target.screen_region.__dict__,
                "client_roi": target.client_roi,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return demo
