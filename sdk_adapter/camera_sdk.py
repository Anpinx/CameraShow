"""Camera SDK — thin facade over the video service layer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sdk_adapter.base import BaseAdapter
from sdk_adapter.device_sdk import DeviceSDK
from sdk_adapter.exceptions import CameraNotFoundError, StreamNotRunningError

if TYPE_CHECKING:
    from video_service.stream_manager import StreamManager


class CameraSDK(BaseAdapter):
    """Coordinates camera device info and stream lifecycle."""

    def __init__(
        self,
        camera_config: dict[str, Any],
        stream_manager: StreamManager,
    ) -> None:
        self._camera_config = camera_config
        self._stream_manager = stream_manager
        self._device = DeviceSDK(camera_config)
        self._ready = False

    def initialize(self) -> None:
        self._device.initialize()
        self._ready = True

    def shutdown(self) -> None:
        self._stream_manager.stop()
        self._device.shutdown()
        self._ready = False

    @property
    def is_ready(self) -> bool:
        return self._ready

    def get_info(self) -> dict[str, Any]:
        return {
            "ip": self._device.get_local_ip(),
            "connected": self._stream_manager.is_running,
            "resolution": self._device.get_resolution_label(),
        }

    def open_stream(self) -> str:
        if not self._ready:
            self.initialize()
        try:
            self._device.probe_camera_available()
        except CameraNotFoundError:
            raise
        return self._stream_manager.start()

    def close_stream(self) -> str:
        self._stream_manager.stop()
        return "offline"

    def get_stream_status(self) -> dict[str, Any]:
        status = self._stream_manager.status
        payload: dict[str, Any] = {"status": status}
        if status == "online":
            payload["streamUrl"] = self._stream_manager.stream_url
        return payload

    def capture_jpeg(self) -> bytes:
        if not self._stream_manager.is_running:
            raise StreamNotRunningError("Stream must be online before capture")
        frame = self._stream_manager.capture_frame()
        if frame is None:
            raise StreamNotRunningError("No frame available for capture")
        return frame
