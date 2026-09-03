from __future__ import annotations

from typing import Any


def install_keyboard_repeat_filter() -> None:
    from pynput import keyboard

    original_listener = keyboard.Listener
    if getattr(original_listener, "_game_demo_filtered", False):
        return

    def filtered_listener(*args: Any, **kwargs: Any):
        on_press = kwargs.get("on_press")
        on_release = kwargs.get("on_release")
        pressed: dict[int, Any] = {}

        def code(key: Any) -> int | None:
            return getattr(key, "vk", None)

        def filtered_press(key: Any):
            value = code(key)
            if value is not None:
                if value in pressed:
                    return None
                pressed[value] = key
            return on_press(key) if on_press else None

        def filtered_release(key: Any):
            value = code(key)
            if value is not None and value not in pressed:
                return None
            if value is not None:
                pressed.pop(value, None)
            return on_release(key) if on_release else None

        kwargs["on_press"] = filtered_press
        kwargs["on_release"] = filtered_release
        listener = original_listener(*args, **kwargs)
        original_stop = listener.stop

        def stop() -> None:
            if on_release:
                for key in list(pressed.values()):
                    on_release(key)
            pressed.clear()
            original_stop()

        listener.stop = stop
        return listener

    filtered_listener._game_demo_filtered = True
    keyboard.Listener = filtered_listener
