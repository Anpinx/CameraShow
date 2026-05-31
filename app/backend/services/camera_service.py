"""Camera and stream orchestration service."""

from __future__ import annotations

import logging
from typing import Any

from app.backend.core.config import get_api_base_url, get_camera_config, get_video_config
from app.backend.core.websocket_manager import WebSocketManager
from app.backend.schemas.camera import CameraInfo, StreamCloseResponse, StreamOpenResponse, StreamStatusResponse
from sdk_adapter.camera_sdk import CameraSDK
from sdk_adapter.exceptions import CameraNotFoundError, SDKError, StreamNotRunningError
from video_service.stream_manager import StreamManager

logger = logging.getLogger(__name__)


class CameraService:
    def __init__(self, ws_manager: WebSocketManager) -> None:
        camera_cfg = get_camera_config().get("camera", {})
        video_cfg = get_video_config().get("video", {})
        self._stream_manager = StreamManager(
            camera_config=camera_cfg,
            video_config=video_cfg,
            api_base_url=get_api_base_url(),
        )
        self._camera_sdk = CameraSDK(camera_cfg, self._stream_manager)
        self._ws_manager = ws_manager
        self._stream_manager.add_status_callback(self._on_stream_status_changed)

    def initialize(self) -> None:
        self._camera_sdk.initialize()
        logger.info("Camera service initialized")

    def shutdown(self) -> None:
        self._camera_sdk.shutdown()
        logger.info("Camera service shutdown")

    def _on_stream_status_changed(self, status: str, extra: dict[str, Any] | None) -> None:
        payload = {"status": status}
        if extra:
            payload.update(extra)
        self._ws_manager.schedule_broadcast("stream.status", payload)

    def get_camera_info(self) -> CameraInfo:
        info = self._camera_sdk.get_info()
        return CameraInfo(**info)

    def open_stream(self) -> StreamOpenResponse:
        try:
            stream_url = self._camera_sdk.open_stream()
        except CameraNotFoundError as exc:
            logger.error("Camera not found: %s", exc)
            raise
        except SDKError as exc:
            logger.error("Failed to open stream: %s", exc)
            raise
        return StreamOpenResponse(streamUrl=stream_url)

    def close_stream(self) -> StreamCloseResponse:
        status = self._camera_sdk.close_stream()
        return StreamCloseResponse(status=status)

    def get_stream_status(self) -> StreamStatusResponse:
        payload = self._camera_sdk.get_stream_status()
        return StreamStatusResponse(**payload)

    @property
    def stream_manager(self) -> StreamManager:
        return self._stream_manager

    def capture_jpeg(self) -> bytes:
        try:
            return self._camera_sdk.capture_jpeg()
        except StreamNotRunningError as exc:
            logger.warning("Capture rejected: %s", exc)
            raise
