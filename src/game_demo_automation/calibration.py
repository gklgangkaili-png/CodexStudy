from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .models import Demonstration, StateMarker


class CalibrationDocument:
    def __init__(self, demonstration: Demonstration) -> None:
        self.demonstration = demonstration

    @classmethod
    def load(cls, path: str | Path) -> CalibrationDocument:
        return cls(Demonstration.load(path))

    def update_state(
        self,
        index: int,
        *,
        name: str | None = None,
        roi: tuple[int, int, int, int] | None = None,
        threshold: float | None = None,
    ) -> StateMarker:
        current = self.demonstration.states[index]
        updated = replace(
            current,
            name=name if name is not None else current.name,
            roi=roi if roi is not None else current.roi,
            threshold=threshold if threshold is not None else current.threshold,
        )
        updated.validate(self.demonstration.window)
        self.demonstration.states[index] = updated
        self.demonstration.calibrated = False
        return updated

    def approve(self) -> None:
        self.demonstration.validate()
        self.demonstration.calibrated = True

    def save(self, path: str | Path) -> None:
        self.demonstration.save(path)
