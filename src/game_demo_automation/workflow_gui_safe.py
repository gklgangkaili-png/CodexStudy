from __future__ import annotations

from . import maa_runtime
from .shared_emergency_stop import SharedF12EmergencyStop


def main() -> None:
    maa_runtime.EmergencyStopHotkey = SharedF12EmergencyStop
    from .workflow_gui import main as workflow_main

    workflow_main()


if __name__ == "__main__":
    main()
