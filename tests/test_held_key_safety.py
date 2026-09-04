from game_demo_automation.held_key_safety_v8 import close_cross_state_key_holds


def test_key_hold_cannot_cross_failing_visual_state() -> None:
    pipeline = {
        "down": {"action": {"type": "KeyDown", "param": {"key": 65}}, "next": ["state"], "attach": {"source_timestamp_ms": 100}},
        "state": {"recognition": {"type": "TemplateMatch"}, "action": {"type": "DoNothing"}, "next": ["up"]},
        "up": {"action": {"type": "KeyUp", "param": {"key": 65}}, "next": [], "attach": {"source_timestamp_ms": 381}},
    }
    close_cross_state_key_holds(pipeline)
    assert pipeline["down"]["action"] == {"type": "LongPressKey", "param": {"key": 65, "duration": 281}}
    assert pipeline["down"]["post_delay"] == 0
    assert pipeline["up"]["action"] == {"type": "DoNothing", "param": {}}
