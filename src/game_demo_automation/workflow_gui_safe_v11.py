from __future__ import annotations

from .maa_runtime_legacy_v4 import MaaLegacyForegroundRunner
from .pipeline_compaction_v7 import compact_key_pairs
from .pynput_filter_v5 import install_keyboard_repeat_filter
from .workflow_gui_safe_v9 import _set_calibration_load_default, _set_new_state_default


def main() -> None:
    from . import region_bundle_calibrated_v3, workflow_gui_safe_v8

    original_compile = region_bundle_calibrated_v3.compile_demonstration

    def compile_compact(demo):
        return compact_key_pairs(original_compile(demo))

    _set_new_state_default()
    _set_calibration_load_default()
    install_keyboard_repeat_filter()
    region_bundle_calibrated_v3.compile_demonstration = compile_compact
    workflow_gui_safe_v8.Maa720pForegroundRunner = MaaLegacyForegroundRunner
    workflow_gui_safe_v8.main()


if __name__ == "__main__":
    main()
