from __future__ import annotations

import tomllib
from pathlib import Path


def test_ui_extra_declares_input_capture_dependency() -> None:
    config = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    ui_dependencies = config["project"]["optional-dependencies"]["ui"]
    assert any(requirement.casefold().startswith("pynput") for requirement in ui_dependencies)
