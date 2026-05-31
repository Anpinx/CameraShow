"""Video stream lifecycle — separated from HTTP API layer."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable

import cv2
import numpy as np

from platform_utils import open_video_capture
from video_service.frame_buffer import FrameBuffer
from video_service.gst_pipeline import (
    build_capture_pipeline,
    configure_gstreamer_env,
    try_import_gst,
)

logger = logging.getLogger(__name__)

StreamStatus = str
StatusCallback = Callable[[StreamStatus, dict[str, Any] | None], None]


class StreamManager:
    """Manages local webcam capture and MJPEG frame buffer."""

    def __init__(
        self,
        camera_config: dict[str, Any],
        video_config: dict[str, Any],
        api_base_url: str,
    ) -> None:
        self._camera_config = camera_config
        self._video_config = video_config
        self._api_base_url = api_base_url.rstrip("/")
        self._frame_buffer = FrameBuffer()
        self._status: StreamStatus = "offline"
        self._worker: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._capture: cv2.VideoCapture | None = None
        self._pipeline = None
        self._status_callbacks: list[StatusCallback] = []
        self._backend = "opencv"
        self._lock = threading.Lock()
        self._use_gstreamer = False

        if video_config.get("prefer_gstreamer", True):
            configure_gstreamer_env(str(video_config.get("gstreamer_bin", "")))
            self._use_gstreamer = try_import_gst() is not None

    @property
    def status(self) -> StreamStatus:
        return self._status

    @property
    def is_running(self) -> bool:
        return self._status == "online"

    @property
    def stream_url(self) -> str:
        return f"{self._api_base_url}/api/stream/mjpeg"

    @property
    def frame_buffer(self) -> FrameBuffer:
        return self._frame_buffer

    def add_status_callback(self, callback: StatusCallback) -> None:
        self._status_callbacks.append(callback)

    def _emit_status(self, status: StreamStatus, extra: dict[str, Any] | None = None) -> None:
        self._status = status
        for callback in self._status_callbacks:
            try:
                callback(status, extra)
            except Exception:  # noqa: BLE001
                logger.exception("Status callback failed")

    def start(self) -> str:
        with self._lock:
            if self._status in {"connecting", "online"}:
                return self.stream_url

            self._emit_status("connecting")
            self._stop_event.clear()
            self._frame_buffer.start()
            self._worker = threading.Thread(target=self._run_capture_loop, daemon=True)
            self._worker.start()

            if not self._frame_buffer.wait_for_frame(timeout=8.0):
                self.stop()
                raise RuntimeError("Failed to start camera stream within timeout")

            self._emit_status("online", {"streamUrl": self.stream_url})
            logger.info("Stream started via %s backend", self._backend)
            return self.stream_url

    def stop(self) -> None:
        with self._lock:
            self._stop_event.set()
            self._frame_buffer.stop()
            if self._capture is not None:
                self._capture.release()
                self._capture = None
            if self._pipeline is not None:
                self._pipeline.set_state(0)
                self._pipeline = None
            if self._worker and self._worker.is_alive():
                self._worker.join(timeout=3.0)
            self._worker = None
            self._emit_status("offline")
            logger.info("Stream stopped")

    def capture_frame(self) -> bytes | None:
        return self._frame_buffer.get_latest()

    def _run_capture_loop(self) -> None:
        if self._try_gstreamer_loop():
            return
        self._opencv_loop()

    def _try_gstreamer_loop(self) -> bool:
        if not self._use_gstreamer:
            return False

        Gst = try_import_gst()
        if Gst is None:
            return False

        try:
            pipeline_str = build_capture_pipeline(Gst, self._camera_config, self._video_config)
            self._pipeline = Gst.parse_launch(pipeline_str)
            sink = self._pipeline.get_by_name("sink")
            if sink is None:
                return False

            self._pipeline.set_state(Gst.State.PLAYING)
            self._backend = "gstreamer"

            while not self._stop_event.is_set():
                sample = sink.emit("try-pull-sample", int(0.2 * Gst.SECOND))
                if sample is None:
                    continue
                buffer = sample.get_buffer()
                success, map_info = buffer.map(Gst.MapFlags.READ)
                if not success:
                    continue
                try:
                    self._frame_buffer.update(bytes(map_info.data))
                finally:
                    buffer.unmap(map_info)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("GStreamer capture failed, falling back to OpenCV: %s", exc)
            if self._pipeline is not None:
                try:
                    self._pipeline.set_state(0)
                except Exception:  # noqa: BLE001
                    pass
                self._pipeline = None
            return False

    def _opencv_loop(self) -> None:
        self._backend = "opencv"
        index = int(self._camera_config.get("device_index", 0))
        width = int(self._camera_config.get("width", 1920))
        height = int(self._camera_config.get("height", 1080))
        quality = int(self._video_config.get("jpeg_quality", 85))
        fps_limit = int(self._video_config.get("mjpeg_fps", 15))
        interval = 1.0 / max(fps_limit, 1)

        self._capture = open_video_capture(index)
        if not self._capture.isOpened():
            logger.error("OpenCV failed to open camera index %s", index)
            return

        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]

        while not self._stop_event.is_set():
            ok, frame = self._capture.read()
            if not ok or frame is None:
                time.sleep(0.05)
                continue
            ok, encoded = cv2.imencode(".jpg", frame, encode_params)
            if ok:
                self._frame_buffer.update(encoded.tobytes())
            time.sleep(interval)

        self._capture.release()
        self._capture = None
