from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic_ns
from typing import Any

from .models import Demonstration, InputEvent, SafetyPolicy, StateMarker, WindowIdentity

FORBIDDEN_VIRTUAL_KEYS = frozenset({0x5B, 0x5C})  # Left/Right Windows key


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read complete JSONL records and ignore a truncated crash-tail record."""
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            break
    return records


class RecordingSession:
    """Crash-tolerant synchronized frame, state, and input event recording."""

    def __init__(self, root: Path, window: WindowIdentity, fps: int = 15) -> None:
        window.validate()
        if fps <= 0:
            raise ValueError("fps must be positive")
        self.root = root
        self.window = window
        self.fps = fps
        self.frames_dir = root / "frames"
        self.templates_dir = root / "templates"
        self.events_path = root / "events.jsonl"
        self.states_path = root / "states.jsonl"
        self.frames_path = root / "frames.jsonl"
        self.metadata_path = root / "metadata.json"
        self._origin_ns = monotonic_ns()
        self._frame_index = 0
        self._closed = False
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path.write_text(
            json.dumps(
                {
                    "format_version": 1,
                    "created_at": datetime.now(UTC).isoformat(),
                    "window": asdict(window),
                    "fps": fps,
                    "timebase": "monotonic milliseconds from recording start",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @property
    def elapsed_ms(self) -> int:
        return (monotonic_ns() - self._origin_ns) // 1_000_000

    def _append(self, path: Path, payload: dict[str, Any]) -> None:
        if self._closed:
            raise RuntimeError("recording session is closed")
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
            stream.write("\n")
            stream.flush()

    def record_event(
        self,
        kind: str,
        *,
        x: int | None = None,
        y: int | None = None,
        key: int | None = None,
        timestamp_ms: int | None = None,
    ) -> InputEvent:
        if key in FORBIDDEN_VIRTUAL_KEYS:
            raise ValueError("system-level Windows keys cannot be recorded")
        event = InputEvent(
            timestamp_ms if timestamp_ms is not None else self.elapsed_ms, kind, x, y, key
        )
        event.validate(self.window)
        self._append(self.events_path, asdict(event))
        return event

    def record_frame(self, png_bytes: bytes, timestamp_ms: int | None = None) -> Path:
        timestamp = timestamp_ms if timestamp_ms is not None else self.elapsed_ms
        filename = f"frame_{self._frame_index:06d}.png"
        frame_path = self.frames_dir / filename
        frame_path.write_bytes(png_bytes)
        self._append(self.frames_path, {"timestamp_ms": timestamp, "file": f"frames/{filename}"})
        self._frame_index += 1
        return frame_path

    def record_state(
        self,
        name: str,
        png_bytes: bytes,
        roi: tuple[int, int, int, int],
        timestamp_ms: int | None = None,
    ) -> StateMarker:
        timestamp = timestamp_ms if timestamp_ms is not None else self.elapsed_ms
        index = len(_read_jsonl(self.states_path))
        filename = f"state_{index:03d}_{name}.png"
        template_path = self.templates_dir / filename
        template_path.write_bytes(png_bytes)
        marker = StateMarker(timestamp, name, str(template_path), roi)
        marker.validate(self.window)
        self._append(self.states_path, asdict(marker))
        return marker

    def close(self) -> None:
        self._closed = True

    def build_demonstration(
        self,
        name: str,
        *,
        calibrated: bool = False,
        safety: SafetyPolicy | None = None,
    ) -> Demonstration:
        events = [InputEvent(**record) for record in _read_jsonl(self.events_path)]
        states = [
            StateMarker(**{**record, "roi": tuple(record["roi"])})
            for record in _read_jsonl(self.states_path)
        ]
        demo = Demonstration(
            name=name,
            window=self.window,
            events=events,
            states=states,
            safety=safety or SafetyPolicy(),
            calibrated=calibrated,
            fps=self.fps,
            video_path=str(self.frames_dir),
        )
        demo.validate()
        demo.save(self.root / "demonstration.json")
        return demo


def recover_demonstration(root: str | Path, name: str = "recovered demonstration") -> Demonstration:
    root = Path(root)
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    session = object.__new__(RecordingSession)
    session.root = root
    session.window = WindowIdentity(**metadata["window"])
    session.fps = metadata["fps"]
    session.events_path = root / "events.jsonl"
    session.states_path = root / "states.jsonl"
    session.frames_dir = root / "frames"
    return session.build_demonstration(name)
