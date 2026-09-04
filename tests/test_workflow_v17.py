from game_demo_automation.workflow_gui_safe_v17 import load_fixed_feature_gui


def test_calibration_dialog_has_isolated_loop_default() -> None:
    namespace = load_fixed_feature_gui("16:9")
    assert namespace["loops"] == 1
    assert namespace["loop_wait_seconds"] == 0.0
    assert callable(namespace["main"])

