from __future__ import annotations

from dataclasses import replace

from .calibration import CalibrationDocument
from .models import StateMarker
from .workflow_gui_safe_v8 import main as v8_main


DEFAULT_TEMPLATE_THRESHOLD = 0.5


def _set_new_state_default() -> None:
    defaults = list(StateMarker.__init__.__defaults__ or ())
    if not defaults:
        raise RuntimeError("无法设置状态模板默认阈值")
    defaults[-1] = DEFAULT_TEMPLATE_THRESHOLD
    StateMarker.__init__.__defaults__ = tuple(defaults)


def _set_calibration_load_default() -> None:
    original_load = CalibrationDocument.load.__func__

    def load_with_threshold(cls, path):
        document = original_load(cls, path)
        document.demonstration.states = [
            replace(state, threshold=DEFAULT_TEMPLATE_THRESHOLD)
            for state in document.demonstration.states
        ]
        return document

    CalibrationDocument.load = classmethod(load_with_threshold)


def main() -> None:
    _set_new_state_default()
    _set_calibration_load_default()
    v8_main()


if __name__ == "__main__":
    main()
