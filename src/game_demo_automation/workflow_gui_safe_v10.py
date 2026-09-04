from __future__ import annotations

from .maa_runtime_legacy_v4 import MaaLegacyForegroundRunner
from .pynput_filter_v5 import install_keyboard_repeat_filter
from .workflow_gui_safe_v9 import _set_calibration_load_default, _set_new_state_default


def main() -> None:
    from . import workflow_gui_safe_v8

    _set_new_state_default()
    _set_calibration_load_default()
    install_keyboard_repeat_filter()
    workflow_gui_safe_v8.Maa720pForegroundRunner = MaaLegacyForegroundRunner
    workflow_gui_safe_v8.main()


if __name__ == "__main__":
    main()
