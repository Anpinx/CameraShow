"""Device and network information SDK."""

from __future__ import annotations

import socket
from typing import Any

from platform_utils import open_video_capture
from sdk_adapter.base import BaseAdapter
from sdk_adapter.exceptions import CameraNotFoundError


class DeviceSDK(BaseAdapter):
    """Provides host network and device metadata."""

    def __init__(self, camera_config: dict[str, Any]) -> None:
        self._camera_config = camera_config
        self._ready = False

    def initialize(self) -> None:
        self._ready = True

    def shutdown(self) -> None:
        self._ready = False

    @property
    def is_ready(self) -> bool:
        return self._ready

    @staticmethod
    def get_local_ip() -> str:
        """Return the primary local IPv4 address of this machine."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except OSError:
            return "127.0.0.1"

    def get_resolution_label(self) -> str:
        width = int(self._camera_config.get("width", 1920))
        height = int(self._camera_config.get("height", 1080))
        if height >= 1080:
            return "1080p"
        if height >= 720:
            return "720p"
        return f"{width}x{height}"

    def probe_camera_available(self) -> bool:
        """Best-effort check whether a camera can be opened."""
        try:
            import cv2  # noqa: F401
        except ImportError:
            return True

        index = int(self._camera_config.get("device_index", 0))
        cap = open_video_capture(index)
        if not cap.isOpened():
            cap.release()
            raise CameraNotFoundError(f"Camera device index {index} is not available")
        cap.release()
        return True
