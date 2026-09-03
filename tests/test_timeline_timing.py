from game_demo_automation.timeline_timing_v12 import normalize_timeline_delays


def test_long_press_duration_is_not_counted_twice() -> None:
    pipeline = {
        "hold": {"action": {"type": "LongPressKey", "param": {"key": 65, "duration": 300}}, "attach": {"source_timestamp_ms": 100}},
        "release_placeholder": {"action": {"type": "DoNothing", "param": {}}, "attach": {"source_timestamp_ms": 400}},
        "click": {"action": {"type": "Click"}, "attach": {"source_timestamp_ms": 550}},
    }
    normalize_timeline_delays(pipeline)
    assert pipeline["hold"]["pre_delay"] == 100
    assert pipeline["release_placeholder"]["pre_delay"] == 0
    assert pipeline["click"]["pre_delay"] == 150
