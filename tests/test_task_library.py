import json

import pytest

from game_demo_automation.task_library import TaskLibrary


def _bundle(path) -> None:
    (path / "pipeline").mkdir(parents=True)
    (path / "task.json").write_text("{}", encoding="utf-8")
    (path / "pipeline" / "main.json").write_text("{}", encoding="utf-8")


def test_external_bundles_remain_visible_in_task_library(tmp_path) -> None:
    default = tmp_path / "default"
    external = tmp_path / "external" / "task-a"
    _bundle(external)
    library = TaskLibrary(tmp_path / "registry.json")
    library.register(external)
    assert library.list(default) == [external.resolve()]
    assert json.loads((tmp_path / "registry.json").read_text(encoding="utf-8"))["bundles"] == [
        str(external.resolve())
    ]


def test_invalid_bundle_cannot_be_registered(tmp_path) -> None:
    library = TaskLibrary(tmp_path / "registry.json")
    with pytest.raises(ValueError, match="不是有效"):
        library.register(tmp_path / "missing")
