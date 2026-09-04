from PySide6.QtGui import QColor, QImage

from game_demo_automation.models import Demonstration, StateMarker, WindowIdentity
from game_demo_automation.portable_bundle import write_portable_task_bundle


def test_generated_bundle_loads_in_maaframework(tmp_path) -> None:
    from maa.resource import Resource
    from maa.toolkit import Toolkit

    templates = []
    for index, color in enumerate(("red", "blue")):
        path = tmp_path / f"template-{index}.png"
        image = QImage(100, 80, QImage.Format.Format_RGB32)
        image.fill(QColor(color))
        assert image.save(str(path), "PNG")
        templates.append(path)
    demo = Demonstration(
        name="maa integration",
        window=WindowIdentity("Game Demo Studio - Simulator", "python.exe", 100, 80),
        events=[],
        states=[
            StateMarker(0, "start", str(templates[0]), (0, 0, 50, 40)),
            StateMarker(100, "end", str(templates[1]), (0, 0, 50, 40)),
        ],
        calibrated=True,
    )
    bundle = write_portable_task_bundle(demo, tmp_path / "bundle")
    Toolkit.init_option(str(tmp_path / "maa-user"))
    resource = Resource()
    job = resource.post_bundle(str(bundle))
    job.wait()
    assert job.succeeded
