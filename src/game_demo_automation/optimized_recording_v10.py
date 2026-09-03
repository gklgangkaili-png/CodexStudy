from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from PySide6.QtGui import QImage

from .models import Demonstration, InputEvent, StateMarker
from .recording import RecordingSession
from .region_capture import RegionTarget, _read_jsonl, derive_state_times


OPTIMIZED_FPS = 3
STATE_MINIMUM_GAP_MS = 1500


def install_jpeg_frame_storage() -> None:
    def record_frame(self, image_bytes: bytes, timestamp_ms: int | None = None) -> Path:
        timestamp = timestamp_ms if timestamp_ms is not None else self.elapsed_ms
        filename = f"frame_{self._frame_index:06d}.jpg"
        frame_path = self.frames_dir / filename
        frame_path.write_bytes(image_bytes)
        self._append(
            self.frames_path,
            {"timestamp_ms": timestamp, "file": f"frames/{filename}"},
        )
        self._frame_index += 1
        return frame_path

    RecordingSession.record_frame = record_frame


def build_optimized_region_draft(
    session: RecordingSession, target: RegionTarget, name: str
) -> Demonstration:
    event_records = _read_jsonl(session.events_path)
    frame_records = _read_jsonl(session.frames_path)
    events = [
        InputEvent(**record)
        for record in event_records
        if record.get("kind") != "mouse_move"
    ]
    frame_times = [int(record["timestamp_ms"]) for record in frame_records]
    state_times = derive_state_times(events, frame_times, STATE_MINIMUM_GAP_MS)
    states: list[StateMarker] = []
    for index, timestamp in enumerate(state_times):
        eligible = [r for r in frame_records if int(r["timestamp_ms"]) <= timestamp]
        record = eligible[-1] if eligible else frame_records[0]
        source = session.root / record["file"]
        template = session.templates_dir / f"state_{index:03d}.png"
        image = QImage(str(source))
        if image.isNull() or not image.save(str(template), "PNG"):
            raise OSError(f"无法生成无损状态模板：{source}")
        states.append(
            StateMarker(timestamp, f"state_{index + 1}", str(template), target.client_roi)
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
                "screen_region": asdict(target.screen_region),
                "client_roi": target.client_roi,
                "frame_format": "JPEG quality 82",
                "state_minimum_gap_ms": STATE_MINIMUM_GAP_MS,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return demo
