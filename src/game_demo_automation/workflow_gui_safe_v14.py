from __future__ import annotations

from pathlib import Path

from .held_key_safety_v8 import close_cross_state_key_holds
from .maa_runtime_legacy_v4 import MaaLegacyForegroundRunner
from .optimized_recording_v10 import (
    OPTIMIZED_FPS,
    build_optimized_region_draft,
    install_jpeg_frame_storage,
)
from .pipeline_compaction_v7 import compact_key_pairs
from .pynput_filter_v5 import install_keyboard_repeat_filter
from .region_bundle_fast_v9 import write_fast_region_bundle
from .workflow_gui_safe_v7 import ASPECT_SIZES
from .workflow_gui_safe_v9 import _set_calibration_load_default, _set_new_state_default


def load_optimized_gui(aspect: str) -> dict:
    width, height = ASPECT_SIZES[aspect]
    v5_path = Path(__file__).with_name("workflow_gui_safe_v5.py")
    source = v5_path.read_text(encoding="utf-8")
    needle = '    source = source_path.read_text(encoding="utf-8")'
    additions = """
    source = source.replace("self.frame_timer.setInterval(1000 // 15)", "self.frame_timer.setInterval(1000 // 3)")
    source = source.replace("RecordingSession(root, self.target.window, fps=15)", "RecordingSession(root, self.target.window, fps=3)")
    source = source.replace('pixmap.save(buffer, "PNG")', 'pixmap.save(buffer, "JPG", 82)')
    source = source.replace("mouse.Listener(on_click=on_click, on_move=on_move)", "mouse.Listener(on_click=on_click)")
""".rstrip()
    source = source.replace(needle, needle + additions)
    source = source.replace("959 if cursor.x()", f"{width - 1} if cursor.x()")
    source = source.replace("719 if cursor.y()", f"{height - 1} if cursor.y()")
    source = source.replace("local.width() != 960", f"local.width() != {width}")
    source = source.replace("local.height() != 720", f"local.height() != {height}")
    source = source.replace("960×720", f"{width}×{height}")
    holder = {
        "__name__": "game_demo_automation.workflow_gui_v14_loader",
        "__package__": "game_demo_automation",
        "__file__": str(v5_path),
    }
    exec(compile(source, str(v5_path), "exec"), holder)
    namespace = holder["_upgraded_gui_namespace"]()
    namespace["build_region_draft"] = build_optimized_region_draft
    return namespace


def main() -> None:
    from . import region_bundle_fast_v9, workflow_gui_safe_v8

    original_compile = region_bundle_fast_v9.compile_demonstration

    def compile_safe(demo):
        return close_cross_state_key_holds(compact_key_pairs(original_compile(demo)))

    _set_new_state_default()
    _set_calibration_load_default()
    install_keyboard_repeat_filter()
    install_jpeg_frame_storage()
    region_bundle_fast_v9.compile_demonstration = compile_safe
    workflow_gui_safe_v8._load_gui = load_optimized_gui
    workflow_gui_safe_v8.write_calibrated_region_bundle = write_fast_region_bundle
    workflow_gui_safe_v8.Maa720pForegroundRunner = MaaLegacyForegroundRunner
    workflow_gui_safe_v8.main()


if __name__ == "__main__":
    main()
