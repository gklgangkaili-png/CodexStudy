from game_demo_automation.workflow_gui import discover_task_bundles


def test_task_library_only_lists_complete_bundles(tmp_path) -> None:
    valid = tmp_path / "valid"
    (valid / "pipeline").mkdir(parents=True)
    (valid / "task.json").write_text("{}", encoding="utf-8")
    (valid / "pipeline" / "main.json").write_text("{}", encoding="utf-8")
    invalid = tmp_path / "invalid"
    invalid.mkdir()
    (invalid / "task.json").write_text("{}", encoding="utf-8")
    assert discover_task_bundles(tmp_path) == [valid]
