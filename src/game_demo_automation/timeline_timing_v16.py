from __future__ import annotations

from typing import Any

CLICK_OVERHEAD_MS = 80


def normalize_interactive_timeline(pipeline: dict[str, Any]) -> dict[str, Any]:
    """Start on the first user action and compensate measured Win32 click cost."""
    nodes = [node for node in pipeline.values() if "source_timestamp_ms" in node.get("attach", {})]
    nodes.sort(key=lambda node: int(node["attach"]["source_timestamp_ms"]))
    if not nodes:
        return pipeline
    cursor = int(nodes[0]["attach"]["source_timestamp_ms"])
    for node in nodes:
        timestamp = int(node["attach"]["source_timestamp_ms"])
        action = node.get("action", {})
        action_type = action.get("type")
        if action_type == "DoNothing":
            node["pre_delay"] = 0
            cursor = max(cursor, timestamp)
            continue
        node["pre_delay"] = max(0, timestamp - cursor)
        node["post_delay"] = 0
        duration = int(action.get("param", {}).get("duration", 0)) if action_type == "LongPressKey" else 0
        overhead = CLICK_OVERHEAD_MS if action_type in {"Click", "ClickKey"} else 0
        cursor = max(cursor, timestamp + duration + overhead)
    return pipeline
