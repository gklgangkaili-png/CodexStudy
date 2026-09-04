from __future__ import annotations

import sys
from pathlib import Path


def _add_source_checkout_to_path() -> None:
    """Allow ``py app_launcher.py`` from an unpacked source checkout."""
    source_root = Path(__file__).resolve().parent / "src"
    if source_root.is_dir() and str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))


def main() -> None:
    _add_source_checkout_to_path()
    if len(sys.argv) > 1 and sys.argv[1].casefold() == "replay":
        del sys.argv[1]
        from game_demo_automation.simulator_replay import main as replay_main

        replay_main()
        return
    from game_demo_automation.workflow_gui_safe_v19 import main as workflow_main

    workflow_main()


if __name__ == "__main__":
    main()
