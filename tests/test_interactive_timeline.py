from game_demo_automation.timeline_timing_v16 import normalize_interactive_timeline


def test_first_action_is_immediate_and_click_cost_does_not_accumulate() -> None:
    pipeline = {
        "first": {"action": {"type": "Click"}, "attach": {"source_timestamp_ms": 765}},
        "second": {"action": {"type": "Click"}, "attach": {"source_timestamp_ms": 1045}},
    }
    normalize_interactive_timeline(pipeline)
    assert pipeline["first"]["pre_delay"] == 0
    assert pipeline["second"]["pre_delay"] == 200
