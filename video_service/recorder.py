"""MJPEG frame stream recorder — writes MP4 from JPEG frames."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

logger = logging.getLogger(__name__)

FrameSupplier = Callable[[], bytes | None]


class StreamRecorder:
    """Background thread that encodes JPEG frames into an MP4 file."""

    def __init__(self, output_path: Path, fps: int, frame_supplier: FrameSupplier) -> None:
        self._output_path = output_path
        self._fps = max(fps, 1)
        self._frame_supplier = frame_supplier
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._writer: cv2.VideoWriter | None = None
        self._frame_count = 0
        self._lock = threading.Lock()
        self._active = False

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._active

    @property
    def frame_count(self) -> int:
        with self._lock:
            return self._frame_count

    @property
    def output_path(self) -> Path:
        return self._output_path

    def start(self) -> None:
        with self._lock:
            if self._active:
                return
            self._active = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self) -> Path:
        self._stop_event.set()
        thread = None
        with self._lock:
            thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=5.0)
        self._release_writer()
        with self._lock:
            self._active = False
            self._thread = None
        return self._output_path

    def _release_writer(self) -> None:
        if self._writer is not None:
            self._writer.release()
            self._writer = None

    def _decode_jpeg(self, jpeg_bytes: bytes) -> np.ndarray | None:
        buffer = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        return frame

    def _run(self) -> None:
        interval = 1.0 / self._fps
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        while not self._stop_event.is_set():
            jpeg = self._frame_supplier()
            if jpeg is None:
                time.sleep(0.05)
                continue

            frame = self._decode_jpeg(jpeg)
            if frame is None:
                time.sleep(0.05)
                continue

            if self._writer is None:
                height, width = frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                self._writer = cv2.VideoWriter(
                    str(self._output_path),
                    fourcc,
                    float(self._fps),
                    (width, height),
                )
                if not self._writer.isOpened():
                    logger.error("Failed to open video writer: %s", self._output_path)
                    break

            self._writer.write(frame)
            with self._lock:
                self._frame_count += 1
            time.sleep(interval)

        self._release_writer()
        logger.info(
            "Recording finished: %s (%s frames)",
            self._output_path,
            self._frame_count,
        )
