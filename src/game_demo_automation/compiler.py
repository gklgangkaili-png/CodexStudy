from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .models import Demonstration, InputEvent


def _action_for_event(event: InputEvent) -> dict[str, Any]:
    if event.kind == "mouse_click":
        return {"type": "Click", "param": {"target": [event.x, event.y]}}
    if event.kind == "key_down":
        return {"type": "KeyDown", "param": {"key": event.key}}
    if event.kind == "key_up":
        return {"type": "KeyUp", "param": {"key": event.key}}
    raise ValueError(f"event kind {event.kind!r} is not executable in the first milestone")


def _slug(index: int, name: str) -> str:
    safe = "_".join(part for part in name.strip().replace("-", " ").split() if part)
    return f"state_{index:03d}_{safe or 'unnamed'}"


def compile_demonstration(demo: Demonstration) -> dict[str, Any]:
    """Compile a calibrated demonstration to MaaFramework Pipeline v2."""
    demo.validate()
    if demo.safety.require_calibrated and not demo.calibrated:
        raise ValueError("demonstration must be calibrated before compilation")
    pipeline: dict[str, Any] = {
        "entry": {
            "recognition": {"type": "DirectHit", "param": {}},
            "action": {"type": "DoNothing", "param": {}},
            "next": [_slug(0, demo.states[0].name)],
            "timeout": demo.safety.step_timeout_ms,
        },
        "safe_pause": {
            "recognition": {"type": "DirectHit", "param": {}},
            "action": {"type": "StopTask", "param": {}},
            "next": [],
        },
    }
    executable = [event for event in demo.events if event.kind != "mouse_move"]
    for state_index, state in enumerate(demo.states):
        state_name = _slug(state_index, state.name)
        next_timestamp = (
            demo.states[state_index + 1].timestamp_ms
            if state_index + 1 < len(demo.states)
            else 2**63 - 1
        )
        state_events = [
            event
            for event in executable
            if state.timestamp_ms <= event.timestamp_ms < next_timestamp
        ]
        next_state = (
            _slug(state_index + 1, demo.states[state_index + 1].name)
            if state_index + 1 < len(demo.states)
            else None
        )
        first_action = f"{state_name}_action_000" if state_events else next_state
        pipeline[state_name] = {
            "recognition": {
                "type": "TemplateMatch",
                "param": {
                    "template": state.template,
                    "roi": list(state.roi),
                    "threshold": state.threshold,
                },
            },
            "action": {"type": "DoNothing", "param": {}},
            "next": [first_action] if first_action else [],
            "timeout": demo.safety.step_timeout_ms,
            "on_error": ["safe_pause"],
            "attach": {"demo_state": state.name, "timestamp_ms": state.timestamp_ms},
        }
        for event_index, event in enumerate(state_events):
            action_name = f"{state_name}_action_{event_index:03d}"
            next_name = (
                f"{state_name}_action_{event_index + 1:03d}"
                if event_index + 1 < len(state_events)
                else next_state
            )
            previous = (
                state.timestamp_ms
                if event_index == 0
                else state_events[event_index - 1].timestamp_ms
            )
            pipeline[action_name] = {
                "recognition": {"type": "DirectHit", "param": {}},
                "action": _action_for_event(event),
                "pre_delay": max(0, event.timestamp_ms - previous),
                "next": [next_name] if next_name else [],
                "on_error": ["safe_pause"],
                "attach": {"source_timestamp_ms": event.timestamp_ms},
            }
    return pipeline


def write_task_bundle(demo: Demonstration, output_dir: str | Path) -> Path:
    pipeline = compile_demonstration(demo)
    root = Path(output_dir)
    pipeline_dir, image_dir = root / "pipeline", root / "image"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    (pipeline_dir / "main.json").write_text(
        json.dumps(pipeline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (root / "demonstration.json").write_text(
        json.dumps(demo.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (root / "safety.json").write_text(
        json.dumps(
            {
                "window": demo.to_dict()["window"],
                "policy": demo.to_dict()["safety"],
                "calibrated": demo.calibrated,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    for state in demo.states:
        source = Path(state.template)
        if source.is_file():
            shutil.copy2(source, image_dir / source.name)
    return root
