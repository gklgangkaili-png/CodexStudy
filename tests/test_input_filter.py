from game_demo_automation.input_filter_v4 import PressedKeyFilter


def test_auto_repeat_is_removed_and_release_is_balanced() -> None:
    keys = PressedKeyFilter()
    assert keys.press(65)
    assert not keys.press(65)
    assert keys.release(65)
    assert not keys.release(65)


def test_stop_releases_every_held_key_once() -> None:
    keys = PressedKeyFilter()
    keys.press(87); keys.press(65)
    assert keys.release_all() == [65, 87]
    assert keys.release_all() == []
