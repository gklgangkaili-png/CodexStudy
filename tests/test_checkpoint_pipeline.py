from game_demo_automation.checkpoint_pipeline_v11 import (
    apply_explicit_checkpoints,
    preserve_global_action_timing,
)


def test_only_initial_and_key_prefixed_states_block_on_vision() -> None:
    pipeline = {
        "state_000_start": {"recognition": {"type": "TemplateMatch"}, "attach": {"demo_state": "start"}},
        "state_001_auto": {"recognition": {"type": "TemplateMatch"}, "attach": {"demo_state": "state_2"}, "on_error": ["safe"]},
        "state_002_boss": {"recognition": {"type": "TemplateMatch"}, "attach": {"demo_state": "key_boss"}},
    }
    apply_explicit_checkpoints(pipeline)
    assert pipeline["state_000_start"]["recognition"]["type"] == "TemplateMatch"
    assert pipeline["state_001_auto"]["recognition"]["type"] == "DirectHit"
    assert "on_error" not in pipeline["state_001_auto"]
    assert pipeline["state_002_boss"]["recognition"]["type"] == "TemplateMatch"


def test_action_timing_is_not_reset_at_each_state() -> None:
    pipeline = {
        "a": {"attach": {"source_timestamp_ms": 100}, "pre_delay": 0, "action": {"type": "Click"}},
        "b": {"attach": {"source_timestamp_ms": 350}, "pre_delay": 0, "action": {"type": "Click"}},
    }
    preserve_global_action_timing(pipeline)
    assert pipeline["a"]["pre_delay"] == 100
    assert pipeline["b"]["pre_delay"] == 250
