from __future__ import annotations

from typing import Any


def normalize_timeline_delays(pipeline: dict[str, Any]) -> dict[str, Any]:
    """Preserve source timing without counting LongPressKey duration twice."""
    nodes = [
        node
        for node in pipeline.values()
        if "source_timestamp_ms" in node.get("attach", {})
    ]
    nodes.sort(key=lambda node: int(node["attach"]["source_timestamp_ms"]))
    cursor = 0
    for node in nodes:
        timestamp = int(node["attach"]["source_timestamp_ms"])
        action = node.get("action", {})
        if action.get("type") == "DoNothing":
            node["pre_delay"] = 0
            cursor = max(cursor, timestamp)
            continue
        node["pre_delay"] = max(0, timestamp - cursor)
        node["post_delay"] = 0
        duration = (
            int(action.get("param", {}).get("duration", 0))
            if action.get("type") == "LongPressKey"
            else 0
        )
        cursor = max(cursor, timestamp + duration)
    return pipeline
