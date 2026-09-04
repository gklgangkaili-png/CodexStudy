from game_demo_automation.shared_emergency_stop import SharedF12EmergencyStop


def test_shared_emergency_stop_rejects_unadvertised_keys() -> None:
    try:
        SharedF12EmergencyStop(lambda: None, virtual_key=0x7A)
    except ValueError as error:
        assert "F12" in str(error)
    else:
        raise AssertionError("non-F12 key should be rejected")
