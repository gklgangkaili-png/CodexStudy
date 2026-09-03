from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1].casefold() == "replay":
        del sys.argv[1]
        from game_demo_automation.simulator_replay import main as replay_main

        replay_main()
        return
    from game_demo_automation.studio import main as studio_main

    studio_main()


if __name__ == "__main__":
    main()
