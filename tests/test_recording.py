import json

import pytest

from game_demo_automation.models import WindowIdentity
from game_demo_automation.recording import RecordingSession, recover_demonstration


def test_recording_session_persists_synchronized_demo(tmp_path) -> None:
    session = RecordingSession(tmp_path, WindowIdentity("Simulator", "python.exe", 960, 540))
    session.record_state("select", b"png-a", (0, 0, 100, 100), timestamp_ms=0)
    session.record_event("mouse_click", x=50, y=60, timestamp_ms=100)
    session.record_frame(b"frame", timestamp_ms=200)
    session.record_state("result", b"png-b", (0, 0, 100, 100), timestamp_ms=1000)
    demo = session.build_demonstration("demo")
    assert demo.events[0].x == 50
    assert demo.states[1].name == "result"
    assert (tmp_path / "frames" / "frame_000000.png").read_bytes() == b"frame"
    assert json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))["fps"] == 15


def test_windows_keys_and_outside_clicks_are_rejected(tmp_path) -> None:
    session = RecordingSession(tmp_path, WindowIdentity("Simulator", "python.exe", 100, 100))
    with pytest.raises(ValueError, match="Windows keys"):
        session.record_event("key_down", key=0x5B)
    with pytest.raises(ValueError, match="inside"):
        session.record_event("mouse_click", x=101, y=50)


def test_recovery_ignores_truncated_jsonl_tail(tmp_path) -> None:
    session = RecordingSession(tmp_path, WindowIdentity("Simulator", "python.exe", 100, 100))
    session.record_state("start", b"a", (0, 0, 10, 10), timestamp_ms=0)
    session.record_event("key_down", key=0x57, timestamp_ms=10)
    session.record_state("end", b"b", (0, 0, 10, 10), timestamp_ms=100)
    with session.events_path.open("a", encoding="utf-8") as stream:
        stream.write('{"timestamp_ms":')
    recovered = recover_demonstration(tmp_path)
    assert len(recovered.events) == 1
    assert [state.name for state in recovered.states] == ["start", "end"]
