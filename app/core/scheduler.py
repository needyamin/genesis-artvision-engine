"""Batch generation scheduler with pause/stop support."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable

from app.video.renderer import RenderControl


@dataclass
class SchedulerState:
    total: int = 0
    completed: int = 0
    current_index: int = 0
    running: bool = False
    unlimited: bool = False


class BatchScheduler:
    """Coordinates sequential batch generation with shared render control."""

    def __init__(self) -> None:
        self.control = RenderControl()
        self.state = SchedulerState()
        self._lock = threading.Lock()
        self._on_state: Callable[[SchedulerState], None] | None = None

    def set_state_callback(self, cb: Callable[[SchedulerState], None]) -> None:
        self._on_state = cb

    def _emit(self) -> None:
        if self._on_state:
            self._on_state(self.state)

    def start(self, total: int, *, unlimited: bool = False) -> None:
        with self._lock:
            self.control = RenderControl()
            self.state = SchedulerState(total=total, unlimited=unlimited, running=True)
            self._emit()

    def mark_video_started(self, index: int) -> None:
        with self._lock:
            self.state.current_index = index
            self._emit()

    def mark_video_done(self) -> None:
        with self._lock:
            self.state.completed += 1
            self._emit()

    def finish(self) -> None:
        with self._lock:
            self.state.running = False
            self._emit()

    def pause(self) -> None:
        self.control.request_pause()

    def resume(self) -> None:
        self.control.request_resume()

    def stop(self) -> None:
        self.control.request_stop()
        with self._lock:
            self.state.running = False
            self._emit()

    @property
    def should_stop(self) -> bool:
        return self.control.stopped
