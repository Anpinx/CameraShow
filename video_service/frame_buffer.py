"""Thread-safe latest-frame buffer for MJPEG and capture."""

from __future__ import annotations

import threading
import time
from typing import Generator, Iterator


class FrameBuffer:
    """Stores the most recent JPEG frame and supports MJPEG streaming."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._frame: bytes | None = None
        self._updated = threading.Event()
        self._running = False

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False
        with self._lock:
            self._frame = None
        self._updated.set()

    @property
    def is_running(self) -> bool:
        return self._running

    def update(self, jpeg_bytes: bytes) -> None:
        with self._lock:
            self._frame = jpeg_bytes
        self._updated.set()

    def get_latest(self) -> bytes | None:
        with self._lock:
            return self._frame

    def wait_for_frame(self, timeout: float = 5.0) -> bytes | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._updated.wait(timeout=0.2):
                self._updated.clear()
                frame = self.get_latest()
                if frame:
                    return frame
        return self.get_latest()

    def iter_mjpeg(self, fps: int = 15) -> Generator[bytes, None, None]:
        interval = 1.0 / max(fps, 1)
        last_frame: bytes | None = None
        while self._running:
            frame = self.get_latest()
            if frame is None:
                time.sleep(0.05)
                continue
            if frame is not last_frame:
                last_frame = frame
                yield frame
            else:
                time.sleep(interval)
