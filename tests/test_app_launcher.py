from __future__ import annotations

import sys
from pathlib import Path

import app_launcher


def test_add_source_checkout_to_path() -> None:
    source_root = str(Path(app_launcher.__file__).resolve().parent / "src")
    original = sys.path.copy()
    try:
        sys.path[:] = [entry for entry in sys.path if entry != source_root]
        app_launcher._add_source_checkout_to_path()
        assert sys.path[0] == source_root
    finally:
        sys.path[:] = original
