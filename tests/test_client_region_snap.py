import game_demo_automation.workflow_gui_safe_v8 as module


def test_v8_exposes_client_snap_boundary() -> None:
    assert callable(module.client_region_under_center)
