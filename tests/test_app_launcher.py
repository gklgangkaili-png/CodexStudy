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


def test_restart_uses_project_virtual_environment(monkeypatch) -> None:
    project_python = Path(app_launcher.__file__).resolve().parent / ".venv" / "Scripts" / "python.exe"
    calls = []
    monkeypatch.setattr(app_launcher, "_project_python", lambda: project_python)
    monkeypatch.setattr(app_launcher.sys, "executable", r"C:\\Python312\\python.exe")
    monkeypatch.setattr(app_launcher.sys, "argv", ["app_launcher.py", "replay"])
    monkeypatch.setattr(app_launcher.os, "execv", lambda executable, args: calls.append((executable, args)))

    app_launcher._restart_in_project_environment()

    assert calls == [
        (
            str(project_python),
            [str(project_python), str(Path(app_launcher.__file__).resolve()), "replay"],
        )
    ]
