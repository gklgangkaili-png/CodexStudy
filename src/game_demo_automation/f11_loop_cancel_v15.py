from __future__ import annotations

import time
from typing import Any

from .maa_runtime_legacy_v4 import MaaLegacyForegroundRunner
from .shared_f11_emergency_stop_v14 import SharedF11EmergencyStop


_cancelled_at = 0.0
CANCEL_WINDOW_SECONDS = 5.0


def mark_loop_cancelled() -> None:
    global _cancelled_at
    _cancelled_at = time.monotonic()


def loop_cancelled_recently() -> bool:
    return _cancelled_at > 0 and time.monotonic() - _cancelled_at < CANCEL_WINDOW_SECONDS


class LoopAwareF11EmergencyStop(SharedF11EmergencyStop):
    def __init__(self, callback, virtual_key: int = 0x7A) -> None:
        def cancel_and_stop() -> None:
            mark_loop_cancelled()
            callback()

        super().__init__(cancel_and_stop, virtual_key)


class LoopAwareMaaRunner(MaaLegacyForegroundRunner):
    def run(self, *args: Any, **kwargs: Any) -> Any:
        if loop_cancelled_recently():
            return {"cancelled_by_f11": True}
        return super().run(*args, **kwargs)
