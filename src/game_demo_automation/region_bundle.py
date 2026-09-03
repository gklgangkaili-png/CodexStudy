from __future__ import annotations

import json
import shutil
from pathlib import Path

from .compiler import compile_demonstration
from .models import Demonstration


def write_region_task_bundle(demo: Demonstration, output_dir: str | Path) -> Path:
    """Export pre-cropped region templates without cropping them a second time."""
    pipeline = compile_demonstration(demo)
    root = Path(output_dir)
    pipeline_dir = root / "pipeline"
    image_dir = root / "image"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    for index, state in enumerate(demo.states):
        source = Path(state.template)
        if not source.is_file():
            raise FileNotFoundError(source)
        filename = f"state_{index:03d}.png"
        shutil.copy2(source, image_dir / filename)
        prefix = f"state_{index:03d}_"
        nodes = [name for name in pipeline if name.startswith(prefix) and "_action_" not in name]
        if len(nodes) != 1:
            raise ValueError(f"无法定位状态节点 {index}")
        pipeline[nodes[0]]["recognition"]["param"]["template"] = filename
    (pipeline_dir / "main.json").write_text(
        json.dumps(pipeline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    demo.save(root / "demonstration.json")
    (root / "task.json").write_text(
        json.dumps(
            {
                "name": demo.name,
                "entry": "entry",
                "window": demo.to_dict()["window"],
                "created_from": "selected screen region",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return root
