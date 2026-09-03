from dataclasses import dataclass

from .models import Demonstration, WindowIdentity


@dataclass(frozen=True)
class RuntimeSnapshot:
    window: WindowIdentity
    is_foreground: bool
    start_state_matched: bool
    emergency_stop_ready: bool
    pressed_keys: frozenset[int] = frozenset()


def preflight_errors(demo: Demonstration, runtime: RuntimeSnapshot) -> list[str]:
    errors: list[str] = []
    if demo.safety.require_calibrated and not demo.calibrated:
        errors.append("任务尚未完成人工校准")
    if runtime.window != demo.window:
        errors.append("目标窗口身份或客户区尺寸不匹配")
    if demo.safety.foreground_only and not runtime.is_foreground:
        errors.append("目标窗口不在前台")
    if not runtime.start_state_matched:
        errors.append("起始关键状态未识别")
    if not runtime.emergency_stop_ready:
        errors.append("紧急停止快捷键不可用")
    if runtime.pressed_keys:
        errors.append("执行前仍有按键处于按下状态")
    return errors
