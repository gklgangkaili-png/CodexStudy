from __future__ import annotations


class PressedKeyFilter:
    def __init__(self) -> None:
        self.pressed: set[int] = set()

    def press(self, key: int) -> bool:
        if key in self.pressed:
            return False
        self.pressed.add(key)
        return True

    def release(self, key: int) -> bool:
        if key not in self.pressed:
            return False
        self.pressed.remove(key)
        return True

    def release_all(self) -> list[int]:
        keys = sorted(self.pressed)
        self.pressed.clear()
        return keys
