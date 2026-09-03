from __future__ import annotations

from .maa_runtime_720p_v3 import Maa720pForegroundRunner


class MaaLegacyForegroundRunner(Maa720pForegroundRunner):
    """Use Maa's LegacyEvent path for foreground Unity/DirectInput-style games."""

    def run(self, *args, **kwargs):
        from maa.controller import MaaWin32InputMethodEnum

        original = MaaWin32InputMethodEnum.Seize
        # Maa720pForegroundRunner resolves the enum member at call time.
        MaaWin32InputMethodEnum._member_map_["Seize"] = MaaWin32InputMethodEnum.LegacyEvent
        try:
            return super().run(*args, **kwargs)
        finally:
            MaaWin32InputMethodEnum._member_map_["Seize"] = original
