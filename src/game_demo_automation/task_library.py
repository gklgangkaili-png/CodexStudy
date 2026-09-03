from __future__ import annotations

import json
from pathlib import Path


def is_task_bundle(path: str | Path) -> bool:
    path = Path(path)
    return (path / "task.json").is_file() and (path / "pipeline" / "main.json").is_file()


class TaskLibrary:
    def __init__(self, registry_path: str | Path) -> None:
        self.registry_path = Path(registry_path)

    def _read(self) -> list[Path]:
        if not self.registry_path.is_file():
            return []
        try:
            payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return [Path(value) for value in payload.get("bundles", [])]

    def register(self, bundle: str | Path) -> None:
        bundle = Path(bundle).resolve()
        if not is_task_bundle(bundle):
            raise ValueError(f"不是有效的 Maa 任务包：{bundle}")
        paths = [path.resolve() for path in self._read() if is_task_bundle(path)]
        if bundle not in paths:
            paths.append(bundle)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(
            json.dumps(
                {"bundles": [str(path) for path in paths]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def list(self, default_root: str | Path) -> list[Path]:
        default_root = Path(default_root)
        paths = []
        if default_root.exists():
            paths.extend(
                path.parent
                for path in default_root.rglob("task.json")
                if is_task_bundle(path.parent)
            )
        paths.extend(path for path in self._read() if is_task_bundle(path))
        unique = {path.resolve(): path.resolve() for path in paths}
        return sorted(unique.values(), key=lambda path: path.stat().st_mtime, reverse=True)

    def last_parent(self, fallback: str | Path) -> Path:
        registered = self._read()
        return registered[-1].parent if registered else Path(fallback)
