from __future__ import annotations

import json
import shutil
from pathlib import Path

from PySide6.QtCore import QRect
from PySide6.QtGui import QImage

from .compiler import compile_demonstration
from .models import Demonstration


def write_fast_region_bundle(demo: Demonstration, output_dir: str | Path) -> Path:
    """Export calibrated templates without re-encoding unchanged PNG files."""
    pipeline = compile_demonstration(demo)
    root = Path(output_dir)
    pipeline_dir, image_dir = root / "pipeline", root / "image"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    for index, state in enumerate(demo.states):
        source = Path(state.template)
        region_file = source.parent.parent / "region.json"
        if not source.is_file() or not region_file.is_file():
            raise OSError(f"状态图或区域元数据无效：{source}")
        base = json.loads(region_file.read_text(encoding="utf-8"))["client_roi"]
        x, y, width, height = state.roi
        relative = QRect(x - base[0], y - base[1], width, height)
        bounds = QRect(0, 0, base[2], base[3])
        if not bounds.contains(relative):
            raise ValueError(f"状态 {state.name} 的 ROI 超出录制区域")
        filename = f"state_{index:03d}.png"
        destination = image_dir / filename
        if relative == bounds:
            shutil.copy2(source, destination)
        else:
            image = QImage(str(source))
            if image.isNull() or not image.copy(relative).save(str(destination), "PNG"):
                raise OSError(f"无法裁剪并保存模板 {filename}")
        prefix = f"state_{index:03d}_"
        nodes = [n for n in pipeline if n.startswith(prefix) and "_action_" not in n]
        if len(nodes) != 1:
            raise ValueError(f"无法定位状态节点 {index}")
        pipeline[nodes[0]]["recognition"]["param"]["template"] = filename
    (pipeline_dir / "main.json").write_text(
        json.dumps(pipeline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    demo.save(root / "demonstration.json")
    (root / "task.json").write_text(
        json.dumps(
            {"name": demo.name, "entry": "entry", "window": demo.to_dict()["window"],
             "maa_display_short_side": 720},
            ensure_ascii=False, indent=2,
        ), encoding="utf-8"
    )
    return root
