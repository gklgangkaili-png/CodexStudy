from __future__ import annotations

from .checkpoint_pipeline_v11 import apply_explicit_checkpoints
from .f11_loop_cancel_v15 import (
    LoopAwareF11EmergencyStop,
    loop_cancelled_recently,
    mark_loop_cancelled,
)
from .held_key_safety_v8 import close_cross_state_key_holds
from .maa_runtime_legacy_v4 import MaaLegacyForegroundRunner
from .optimized_recording_v10 import install_jpeg_frame_storage
from .pipeline_compaction_v7 import compact_key_pairs
from .pynput_filter_v5 import install_keyboard_repeat_filter
from .region_bundle_fast_v9 import write_fast_region_bundle
from .shared_f11_emergency_stop_v14 import SharedF11EmergencyStop
from .timeline_timing_v12 import normalize_timeline_delays
from .workflow_gui_safe_v9 import _set_calibration_load_default, _set_new_state_default
from .workflow_gui_safe_v16 import load_feature_gui


def load_fixed_feature_gui(aspect: str) -> dict:
    namespace = load_feature_gui(aspect)
    # v16 injected an unused loops assignment into CalibrationDialog.__init__.
    # Supplying the calibration default keeps that dialog isolated while
    # RunWorker continues to receive its explicit user-selected loop count.
    namespace["loops"] = 1
    namespace["loop_wait_seconds"] = 0.0
    namespace["SharedF12EmergencyStop"] = LoopAwareF11EmergencyStop
    namespace["mark_loop_cancelled"] = mark_loop_cancelled
    namespace["loop_cancelled_recently"] = loop_cancelled_recently
    return namespace


def main() -> None:
    from . import region_bundle_fast_v9, workflow_gui_safe_v8

    original_compile = region_bundle_fast_v9.compile_demonstration

    def compile_checkpointed(demo):
        pipeline = compact_key_pairs(original_compile(demo))
        pipeline = close_cross_state_key_holds(pipeline)
        pipeline = apply_explicit_checkpoints(pipeline)
        return normalize_timeline_delays(pipeline)

    _set_new_state_default()
    _set_calibration_load_default()
    install_keyboard_repeat_filter()
    install_jpeg_frame_storage()
    region_bundle_fast_v9.compile_demonstration = compile_checkpointed
    workflow_gui_safe_v8._load_gui = load_fixed_feature_gui
    workflow_gui_safe_v8.write_calibrated_region_bundle = write_fast_region_bundle
    workflow_gui_safe_v8.Maa720pForegroundRunner = MaaLegacyForegroundRunner
    workflow_gui_safe_v8.SharedF12EmergencyStop = SharedF11EmergencyStop
    workflow_gui_safe_v8.main()


if __name__ == "__main__":
    main()


