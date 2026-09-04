from __future__ import annotations

import ast
from pathlib import Path


def _method(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"method not found: {name}")


def _clears_worker(method: ast.FunctionDef) -> bool:
    for node in ast.walk(method):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == "worker"
            for target in targets
        ):
            return True
    return False


def test_worker_is_released_only_after_qthread_finished() -> None:
    tree = ast.parse(Path("src/game_demo_automation/workflow_gui.py").read_text(encoding="utf-8"))
    execute = ast.unparse(_method(tree, "execute_selected"))
    assert "worker.finished.connect(self.execution_worker_finished)" in execute
    assert not _clears_worker(_method(tree, "execution_completed"))
    assert not _clears_worker(_method(tree, "execution_failed"))
    assert _clears_worker(_method(tree, "execution_worker_finished"))
