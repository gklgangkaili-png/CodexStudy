from types import SimpleNamespace

from game_demo_automation.key_mapping_v13 import windows_virtual_key


def test_escape_maps_to_windows_virtual_key() -> None:
    esc = object()
    keyboard = SimpleNamespace(
        Key=SimpleNamespace(
            esc=esc, enter=object(), tab=object(), space=object(), backspace=object(),
            delete=object(), up=object(), down=object(), left=object(), right=object(),
        )
    )
    assert windows_virtual_key(esc, keyboard) == 0x1B


def test_regular_virtual_key_is_preserved() -> None:
    keyboard = SimpleNamespace(Key=SimpleNamespace())
    assert windows_virtual_key(SimpleNamespace(vk=87), keyboard) == 87
