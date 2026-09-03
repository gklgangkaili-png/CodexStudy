from __future__ import annotations

from typing import Any


def compact_key_pairs(pipeline: dict[str, Any]) -> dict[str, Any]:
    """Compile adjacent KeyDown/KeyUp nodes into one duration-accurate action."""
    removable: set[str] = set()
    for name, node in list(pipeline.items()):
        action = node.get("action", {})
        if action.get("type") != "KeyDown":
            continue
        next_names = node.get("next", [])
        if len(next_names) != 1 or next_names[0] not in pipeline:
            continue
        release_name = next_names[0]
        release = pipeline[release_name]
        release_action = release.get("action", {})
        if (
            release_action.get("type") != "KeyUp"
            or release_action.get("param", {}).get("key")
            != action.get("param", {}).get("key")
        ):
            continue
        start_ms = int(node.get("attach", {}).get("source_timestamp_ms", 0))
        end_ms = int(release.get("attach", {}).get("source_timestamp_ms", start_ms))
        duration = max(0, end_ms - start_ms)
        key = action["param"]["key"]
        node["action"] = (
            {"type": "ClickKey", "param": {"key": key}}
            if duration == 0
            else {"type": "LongPressKey", "param": {"key": key, "duration": duration}}
        )
        node["next"] = release.get("next", [])
        node["post_delay"] = 0
        removable.add(release_name)
    for name in removable:
        pipeline.pop(name, None)
    for node in pipeline.values():
        action_type = node.get("action", {}).get("type")
        if action_type not in {"DoNothing", "StopTask"}:
            node.setdefault("post_delay", 0)
    return pipeline
