from __future__ import annotations

import argparse
import time
from pathlib import Path

from .maa_runtime import MaaForegroundRunner
from .models import Demonstration
from .portable_bundle import write_portable_task_bundle

SIMULATOR_TITLE = "Game Demo Studio - Simulator"


def prepare_simulator_bundle(demonstration_path: str | Path) -> tuple[Demonstration, Path]:
    demo_path = Path(demonstration_path).resolve()
    demo = Demonstration.load(demo_path)
    if demo.window.title != SIMULATOR_TITLE or demo.window.executable.casefold() != "python.exe":
        raise RuntimeError("当前阶段只允许回放 Game Demo Studio 模拟窗口")
    if not demo.calibrated:
        raise RuntimeError("示教尚未在校准编辑器中确认")
    bundle = write_portable_task_bundle(demo, demo_path.parent / "maa-bundle")
    return demo, bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a calibrated demonstration in Studio")
    parser.add_argument("demonstration", help="path to calibrated demonstration.json")
    parser.add_argument("--countdown", type=int, default=3)
    args = parser.parse_args()
    demo, bundle = prepare_simulator_bundle(args.demonstration)
    if args.countdown < 1:
        raise SystemExit("countdown must be at least one second")
    print(f"Maa bundle: {bundle}")
    print(f"请在 {args.countdown} 秒内切换到 Studio，并保持窗口前台。F12 可紧急停止。")
    for remaining in range(args.countdown, 0, -1):
        print(remaining, flush=True)
        time.sleep(1)
    runner = MaaForegroundRunner(demo_path_dir(bundle) / "maa-user")
    result = runner.run(bundle, demo.window)
    print(f"任务结束：{result}")


def demo_path_dir(bundle: Path) -> Path:
    return bundle.parent


if __name__ == "__main__":
    main()
