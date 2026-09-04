from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


def close_cross_state_key_holds(pipeline: dict[str, Any]) -> dict[str, Any]:
    """Ensure no KeyDown can remain held while a later state waits for recognition."""
    downs: dict[int, deque[tuple[str, dict[str, Any]]]] = defaultdict(deque)
    ordered = sorted(
        pipeline.items(),
        key=lambda item: int(item[1].get("attach", {}).get("source_timestamp_ms", 2**63 - 1)),
    )
    for name, node in ordered:
        action = node.get("action", {})
        action_type = action.get("type")
        key = action.get("param", {}).get("key")
        if action_type == "KeyDown" and isinstance(key, int):
            downs[key].append((name, node))
        elif action_type == "KeyUp" and isinstance(key, int) and downs[key]:
            _down_name, down = downs[key].popleft()
            start = int(down.get("attach", {}).get("source_timestamp_ms", 0))
            end = int(node.get("attach", {}).get("source_timestamp_ms", start))
            down["action"] = {
                "type": "LongPressKey",
                "param": {"key": key, "duration": max(1, end - start)},
            }
            down["post_delay"] = 0
            node["action"] = {"type": "DoNothing", "param": {}}
            node["post_delay"] = 0
    for key, pending in downs.items():
        for _name, node in pending:
            node["action"] = {"type": "ClickKey", "param": {"key": key}}
            node["post_delay"] = 0
    return pipeline
