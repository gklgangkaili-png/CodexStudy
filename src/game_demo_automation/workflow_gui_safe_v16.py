from __future__ import annotations

from pathlib import Path

from .checkpoint_pipeline_v11 import apply_explicit_checkpoints
from .held_key_safety_v8 import close_cross_state_key_holds
from .key_mapping_v13 import windows_virtual_key
from .maa_runtime_legacy_v4 import MaaLegacyForegroundRunner
from .optimized_recording_v10 import build_optimized_region_draft, install_jpeg_frame_storage
from .pipeline_compaction_v7 import compact_key_pairs
from .pynput_filter_v5 import install_keyboard_repeat_filter
from .region_bundle_fast_v9 import write_fast_region_bundle
from .shared_f11_emergency_stop_v14 import SharedF11EmergencyStop
from .timeline_timing_v12 import normalize_timeline_delays
from .workflow_gui_safe_v7 import ASPECT_SIZES
from .workflow_gui_safe_v9 import _set_calibration_load_default, _set_new_state_default


def load_feature_gui(aspect: str) -> dict:
    width, height = ASPECT_SIZES[aspect]
    v5_path = Path(__file__).with_name("workflow_gui_safe_v5.py")
    source = v5_path.read_text(encoding="utf-8")
    needle = '    source = source_path.read_text(encoding="utf-8")'
    additions = """
    source = source.replace("self.frame_timer.setInterval(1000 // 15)", "self.frame_timer.setInterval(1000 // 3)")
    source = source.replace("RecordingSession(root, self.target.window, fps=15)", "RecordingSession(root, self.target.window, fps=3)")
    source = source.replace('pixmap.save(buffer, "PNG")', 'pixmap.save(buffer, "JPG", 82)')
    source = source.replace("mouse.Listener(on_click=on_click, on_move=on_move)", "mouse.Listener(on_click=on_click)")
    source = source.replace('            QPushButton,', '            QPushButton,\\n            QDoubleSpinBox,\\n            QSpinBox,')
    source = source.replace('            def key_code(key):\\n                return getattr(key, "vk", None)', '            def key_code(key):\\n                return windows_virtual_key(key, keyboard)')
    source = source.replace('        def __init__(self, bundle: Path, demo_path: Path) -> None:', '        def __init__(self, bundle: Path, demo_path: Path, loops: int, loop_wait_seconds: float) -> None:')
    source = source.replace('            self.demo_path = demo_path', '            self.demo_path = demo_path\\n            self.loops = loops\\n            self.loop_wait_seconds = loop_wait_seconds')
    source = source.replace('                result = MaaForegroundRunner(self.bundle / "maa-user").run(self.bundle, demo.window)\\n                self.completed.emit(str(result))', '                results = []\\n                for loop_index in range(self.loops):\\n                    self.message.emit(f"正在执行第 {loop_index + 1}/{self.loops} 轮")\\n                    result = MaaForegroundRunner(self.bundle / "maa-user").run(self.bundle, demo.window)\\n                    results.append(result)\\n                    if isinstance(result, dict) and result.get("cancelled_by_f11"):\\n                        break\\n                    if loop_index + 1 < self.loops and self.loop_wait_seconds > 0:\\n                        self.message.emit(f"下一轮将在 {self.loop_wait_seconds:g} 秒后开始（F11 可取消）")\\n                        deadline = time.monotonic() + self.loop_wait_seconds\\n                        with SharedF12EmergencyStop(mark_loop_cancelled):\\n                            while time.monotonic() < deadline:\\n                                if loop_cancelled_recently():\\n                                    self.completed.emit(str(results))\\n                                    return\\n                                time.sleep(min(0.1, deadline - time.monotonic()))\\n                self.completed.emit(str(results))')
    source = source.replace('            self.add_task_selector(layout)', '            self.add_task_selector(layout)\\n            loop_row = QHBoxLayout()\\n            loop_row.addWidget(QLabel("循环次数"))\\n            self.loop_count = QSpinBox()\\n            self.loop_count.setRange(1, 20)\\n            self.loop_count.setValue(1)\\n            loop_row.addWidget(self.loop_count)\\n            loop_row.addWidget(QLabel("每轮等待（秒）"))\\n            self.loop_wait_seconds = QDoubleSpinBox()\\n            self.loop_wait_seconds.setRange(0, 3600)\\n            self.loop_wait_seconds.setDecimals(1)\\n            self.loop_wait_seconds.setSingleStep(0.5)\\n            self.loop_wait_seconds.setValue(0)\\n            loop_row.addWidget(self.loop_wait_seconds)\\n            loop_row.addStretch(1)\\n            layout.addLayout(loop_row)')
    source = source.replace('worker = RunWorker(bundle, bundle / "demonstration.json")', 'worker = RunWorker(bundle, bundle / "demonstration.json", self.loop_count.value(), self.loop_wait_seconds.value())')
    source = source.replace("F12 紧急停止", "F11 紧急停止")
""".rstrip()
    source = source.replace(needle, needle + additions)
    source = source.replace("959 if cursor.x()", f"{width - 1} if cursor.x()")
    source = source.replace("719 if cursor.y()", f"{height - 1} if cursor.y()")
    source = source.replace("local.width() != 960", f"local.width() != {width}")
    source = source.replace("local.height() != 720", f"local.height() != {height}")
    source = source.replace("960×720", f"{width}×{height}")
    holder = {"__name__": "game_demo_automation.workflow_gui_v16_loader", "__package__": "game_demo_automation", "__file__": str(v5_path)}
    exec(compile(source, str(v5_path), "exec"), holder)
    namespace = holder["_upgraded_gui_namespace"]()
    namespace["build_region_draft"] = build_optimized_region_draft
    namespace["windows_virtual_key"] = windows_virtual_key
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
    workflow_gui_safe_v8._load_gui = load_feature_gui
    workflow_gui_safe_v8.write_calibrated_region_bundle = write_fast_region_bundle
    workflow_gui_safe_v8.Maa720pForegroundRunner = MaaLegacyForegroundRunner
    workflow_gui_safe_v8.SharedF12EmergencyStop = SharedF11EmergencyStop
    workflow_gui_safe_v8.main()


if __name__ == "__main__":
    main()

