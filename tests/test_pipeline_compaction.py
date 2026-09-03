from game_demo_automation.pipeline_compaction_v7 import compact_key_pairs


def test_tap_becomes_one_click_key_without_maa_delay() -> None:
    pipeline = {
        "down": {"action": {"type": "KeyDown", "param": {"key": 87}}, "next": ["up"], "attach": {"source_timestamp_ms": 10}},
        "up": {"action": {"type": "KeyUp", "param": {"key": 87}}, "next": ["done"], "attach": {"source_timestamp_ms": 10}},
        "done": {"action": {"type": "DoNothing"}, "next": []},
    }
    compact_key_pairs(pipeline)
    assert pipeline["down"]["action"] == {"type": "ClickKey", "param": {"key": 87}}
    assert pipeline["down"]["post_delay"] == 0
    assert pipeline["down"]["next"] == ["done"]
    assert "up" not in pipeline


def test_held_key_preserves_recorded_duration() -> None:
    pipeline = {
        "down": {"action": {"type": "KeyDown", "param": {"key": 87}}, "next": ["up"], "attach": {"source_timestamp_ms": 100}},
        "up": {"action": {"type": "KeyUp", "param": {"key": 87}}, "next": [], "attach": {"source_timestamp_ms": 147}},
    }
    compact_key_pairs(pipeline)
    assert pipeline["down"]["action"] == {"type": "LongPressKey", "param": {"key": 87, "duration": 47}}
