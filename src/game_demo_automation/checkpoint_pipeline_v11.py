from __future__ import annotations

from typing import Any


def apply_explicit_checkpoints(pipeline: dict[str, Any]) -> dict[str, Any]:
    """Only the initial state and explicitly named key_* states block on vision."""
    for name, node in pipeline.items():
        attach = node.get("attach", {})
        if "demo_state" not in attach:
            continue
        is_initial = name.startswith("state_000_")
        is_explicit = str(attach["demo_state"]).casefold().startswith("key_")
        if not (is_initial or is_explicit):
            node["recognition"] = {"type": "DirectHit", "param": {}}
            node.pop("on_error", None)
        node["pre_delay"] = 0
        node["post_delay"] = 0
    return pipeline


def preserve_global_action_timing(pipeline: dict[str, Any]) -> dict[str, Any]:
    """Keep event intervals when actions are distributed across candidate states."""
    actions = [
        node
        for node in pipeline.values()
        if "source_timestamp_ms" in node.get("attach", {})
    ]
    actions.sort(key=lambda node: int(node["attach"]["source_timestamp_ms"]))
    previous = 0
    for node in actions:
        timestamp = int(node["attach"]["source_timestamp_ms"])
        node["pre_delay"] = max(0, timestamp - previous)
        node["post_delay"] = 0
        previous = timestamp
    return pipeline
