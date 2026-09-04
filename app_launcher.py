from __future__ import annotations

import os
import sys
from pathlib import Path


def _project_python() -> Path | None:
    candidate = Path(__file__).resolve().parent / ".venv" / "Scripts" / "python.exe"
    return candidate if candidate.is_file() else None


def _restart_in_project_environment() -> None:
    """Use the repository virtual environment when launched with global Python."""
    project_python = _project_python()
    if project_python is None or Path(sys.executable).resolve() == project_python.resolve():
        return
    os.execv(
        str(project_python),
        [str(project_python), str(Path(__file__).resolve()), *sys.argv[1:]],
    )


def _add_source_checkout_to_path() -> None:
    """Allow ``py app_launcher.py`` from an unpacked source checkout."""
    source_root = Path(__file__).resolve().parent / "src"
    if source_root.is_dir() and str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))


def main() -> None:
    _restart_in_project_environment()
    _add_source_checkout_to_path()
    try:
        if len(sys.argv) > 1 and sys.argv[1].casefold() == "replay":
            del sys.argv[1]
            from game_demo_automation.simulator_replay import main as replay_main

            replay_main()
            return
        from game_demo_automation.workflow_gui_safe_v19 import main as workflow_main
    except ModuleNotFoundError as exc:
        if exc.name in {"PySide6", "maa"}:
            raise SystemExit(
                "项目依赖未安装。请运行：.\\.venv\\Scripts\\python.exe -m pip install -e \".[ui,maa]\""
            ) from None
        raise
    workflow_main()


if __name__ == "__main__":
    main()
