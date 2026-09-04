from __future__ import annotations

import json
import shutil
from pathlib import Path

from .compiler import compile_demonstration
from .models import Demonstration


def _crop_template(source: Path, destination: Path, roi: tuple[int, int, int, int]) -> None:
    try:
        from PySide6.QtGui import QImage
    except ImportError as exc:
        raise RuntimeError("PySide6 is required to crop recorded state templates") from exc
    image = QImage(str(source))
    if image.isNull():
        raise ValueError(f"cannot decode state template: {source}")
    x, y, width, height = roi
    cropped = image.copy(x, y, width, height)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not cropped.save(str(destination), "PNG"):
        raise OSError(f"cannot save cropped state template: {destination}")


def write_portable_task_bundle(demo: Demonstration, output_dir: str | Path) -> Path:
    """Write a self-contained Maa bundle with cropped, relative templates."""
    pipeline = compile_demonstration(demo)
    root = Path(output_dir)
    pipeline_dir = root / "pipeline"
    image_dir = root / "image"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    for index, state in enumerate(demo.states):
        source = Path(state.template)
        if not source.is_file():
            raise FileNotFoundError(f"state template does not exist: {source}")
        portable_name = f"state_{index:03d}.png"
        _crop_template(source, image_dir / portable_name, state.roi)
        node_prefix = f"state_{index:03d}_"
        matching_nodes = [
            name for name in pipeline if name.startswith(node_prefix) and "_action_" not in name
        ]
        if len(matching_nodes) != 1:
            raise ValueError(f"cannot resolve pipeline node for state index {index}")
        pipeline[matching_nodes[0]]["recognition"]["param"]["template"] = portable_name

    (pipeline_dir / "main.json").write_text(
        json.dumps(pipeline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    demo.save(root / "demonstration.json")
    (root / "safety.json").write_text(
        json.dumps(
            {
                "window": demo.to_dict()["window"],
                "policy": demo.to_dict()["safety"],
                "calibrated": demo.calibrated,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    license_source = (
        Path(__file__).parents[2] / "docs" / "adr" / "0001-use-maaframework-as-execution-core.md"
    )
    if license_source.is_file():
        shutil.copy2(license_source, root / "ARCHITECTURE.md")
    return root
