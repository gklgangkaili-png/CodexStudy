from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

EventKind = Literal["mouse_click", "key_down", "key_up", "mouse_move"]


@dataclass(frozen=True)
class WindowIdentity:
    title: str
    executable: str
    client_width: int
    client_height: int

    def validate(self) -> None:
        if not self.title.strip() or not self.executable.strip():
            raise ValueError("window title and executable are required")
        if self.client_width <= 0 or self.client_height <= 0:
            raise ValueError("client dimensions must be positive")


@dataclass(frozen=True)
class InputEvent:
    timestamp_ms: int
    kind: EventKind
    x: int | None = None
    y: int | None = None
    key: int | None = None

    def validate(self, window: WindowIdentity) -> None:
        if self.timestamp_ms < 0:
            raise ValueError("event timestamp cannot be negative")
        if self.kind in {"mouse_click", "mouse_move"}:
            if self.x is None or self.y is None:
                raise ValueError(f"{self.kind} requires x and y")
            if not (0 <= self.x < window.client_width and 0 <= self.y < window.client_height):
                raise ValueError("mouse event must stay inside the target client area")
        if self.kind in {"key_down", "key_up"} and self.key is None:
            raise ValueError(f"{self.kind} requires a Windows virtual-key code")


@dataclass(frozen=True)
class StateMarker:
    timestamp_ms: int
    name: str
    template: str
    roi: tuple[int, int, int, int]
    threshold: float = 0.82

    def validate(self, window: WindowIdentity) -> None:
        if self.timestamp_ms < 0 or not self.name.strip() or not self.template.strip():
            raise ValueError("state marker requires timestamp, name, and template")
        x, y, width, height = self.roi
        if width <= 0 or height <= 0:
            raise ValueError("state ROI must have positive dimensions")
        if x < 0 or y < 0 or x + width > window.client_width or y + height > window.client_height:
            raise ValueError("state ROI must be inside the target client area")
        if not 0 < self.threshold <= 1:
            raise ValueError("template threshold must be in (0, 1]")


@dataclass(frozen=True)
class SafetyPolicy:
    emergency_stop_key: int = 0x7B
    step_timeout_ms: int = 10_000
    max_retries: int = 2
    max_runtime_ms: int = 1_800_000
    max_loops: int = 20
    foreground_only: bool = True
    require_calibrated: bool = True

    def validate(self) -> None:
        if self.step_timeout_ms <= 0 or self.max_runtime_ms <= 0:
            raise ValueError("timeouts must be positive")
        if self.max_retries < 0 or self.max_loops <= 0:
            raise ValueError("retry and loop limits are invalid")


@dataclass
class Demonstration:
    name: str
    window: WindowIdentity
    events: list[InputEvent]
    states: list[StateMarker]
    safety: SafetyPolicy = field(default_factory=SafetyPolicy)
    calibrated: bool = False
    fps: int = 15
    video_path: str | None = None

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("demonstration name is required")
        if self.fps <= 0:
            raise ValueError("fps must be positive")
        self.window.validate()
        self.safety.validate()
        for event in self.events:
            event.validate(self.window)
        for state in self.states:
            state.validate(self.window)
        if len(self.states) < 2:
            raise ValueError("at least two state markers are required")
        if self.states != sorted(self.states, key=lambda item: item.timestamp_ms):
            raise ValueError("state markers must be chronological")
        if self.events != sorted(self.events, key=lambda item: item.timestamp_ms):
            raise ValueError("input events must be chronological")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Demonstration:
        return cls(
            name=data["name"],
            window=WindowIdentity(**data["window"]),
            events=[InputEvent(**event) for event in data.get("events", [])],
            states=[
                StateMarker(**{**state, "roi": tuple(state["roi"])})
                for state in data.get("states", [])
            ],
            safety=SafetyPolicy(**data.get("safety", {})),
            calibrated=data.get("calibrated", False),
            fps=data.get("fps", 15),
            video_path=data.get("video_path"),
        )

    @classmethod
    def load(cls, path: str | Path) -> Demonstration:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
