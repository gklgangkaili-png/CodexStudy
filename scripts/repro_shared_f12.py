from __future__ import annotations

import ctypes

from game_demo_automation.shared_emergency_stop import SharedF12EmergencyStop


def main() -> int:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    hotkey_id = 0x7A13
    if not user32.RegisterHotKey(None, hotkey_id, 0, 0x7B):
        error = ctypes.get_last_error()
        if error != 1409:
            print(f"cannot prepare conflict: winerror={error}")
            return 2
    monitor = SharedF12EmergencyStop(lambda: None)
    try:
        monitor.start()
        print("shared_f12_listener=True")
        return 0
    finally:
        monitor.close()
        user32.UnregisterHotKey(None, hotkey_id)


if __name__ == "__main__":
    raise SystemExit(main())
