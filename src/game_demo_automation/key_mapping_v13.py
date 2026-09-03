from __future__ import annotations

from typing import Any


def windows_virtual_key(key: Any, keyboard: Any) -> int | None:
    value = getattr(key, "vk", None)
    if value is not None:
        return int(value)
    special = {
        keyboard.Key.esc: 0x1B,
        keyboard.Key.enter: 0x0D,
        keyboard.Key.tab: 0x09,
        keyboard.Key.space: 0x20,
        keyboard.Key.backspace: 0x08,
        keyboard.Key.delete: 0x2E,
        keyboard.Key.up: 0x26,
        keyboard.Key.down: 0x28,
        keyboard.Key.left: 0x25,
        keyboard.Key.right: 0x27,
    }
    return special.get(key)
