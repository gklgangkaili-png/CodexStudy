from __future__ import annotations

import ctypes


def main() -> int:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    hotkey_id = 0x7A12
    ctypes.set_last_error(0)
    registered = bool(user32.RegisterHotKey(None, hotkey_id, 0, 0x7B))
    error = ctypes.get_last_error()
    print(f"registered={registered} winerror={error}")
    if registered:
        user32.UnregisterHotKey(None, hotkey_id)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
