import game_demo_automation.f11_loop_cancel_v15 as module


def test_f11_cancellation_blocks_immediate_next_loop(monkeypatch) -> None:
    monkeypatch.setattr(module.time, "monotonic", lambda: 100.0)
    module.mark_loop_cancelled()
    assert module.loop_cancelled_recently()
    monkeypatch.setattr(module.time, "monotonic", lambda: 106.0)
    assert not module.loop_cancelled_recently()
