from __future__ import annotations

import re
import sys
from pathlib import Path


def latest_log(tasks_root: Path) -> Path:
    logs = list(tasks_root.glob("*/maa-user/debug/maafw.log"))
    if not logs:
        raise FileNotFoundError("没有找到 Maa 运行日志")
    return max(logs, key=lambda path: path.stat().st_mtime)


def diagnose(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    scores = [float(value) for value in re.findall(r'"score":([0-9.]+)', text)]
    action_successes = len(re.findall(r"Node\.Action\.Succeeded", text))
    recognition_successes = len(re.findall(r"Node\.Recognition\.Succeeded", text))
    task_failed = "Tasker.Task.Failed" in text
    print(f"log={path}")
    print(f"max_score={max(scores) if scores else 'none'}")
    print(f"recognition_successes={recognition_successes}")
    print(f"action_successes={action_successes}")
    print(f"task_failed={task_failed}")
    if action_successes == 0:
        print("VERDICT=RED: Maa 没有执行任何动作")
        return 1
    print("VERDICT=GREEN: Maa 至少执行了一个动作")
    return 0


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "tasks"
    raise SystemExit(diagnose(latest_log(root)))
