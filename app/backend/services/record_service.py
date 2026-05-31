"""Video recording orchestration."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.backend.core.config import get_app_config, get_video_config
from app.backend.services.settings_service import SettingsService
from sdk_adapter.exceptions import (
    RecordingAlreadyActiveError,
    RecordingError,
    RecordingNotActiveError,
    StreamNotRunningError,
)
from video_service.recorder import StreamRecorder
from video_service.stream_manager import StreamManager

logger = logging.getLogger(__name__)


class RecordService:
    def __init__(self, settings_service: SettingsService) -> None:
        self._settings = settings_service
        video_cfg = get_video_config().get("video", {})
        self._fps = int(video_cfg.get("record_fps", video_cfg.get("mjpeg_fps", 15)))
        self._recorder: StreamRecorder | None = None
        self._started_at: str | None = None
        self._filename: str | None = None

    def _build_output_path(self) -> Path:
        save_dir = Path(self._settings.record_save_path)
        save_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"record_{timestamp}.mp4"
        return save_dir / filename

    def start(self, stream_manager: StreamManager) -> dict[str, Any]:
        if not stream_manager.is_running:
            raise StreamNotRunningError("Video stream is not active")
        if self._recorder is not None and self._recorder.is_active:
            raise RecordingAlreadyActiveError("Recording is already in progress")

        output_path = self._build_output_path()
        self._filename = output_path.name
        self._started_at = datetime.now(timezone.utc).isoformat()
        self._recorder = StreamRecorder(
            output_path=output_path,
            fps=self._fps,
            frame_supplier=stream_manager.capture_frame,
        )
        self._recorder.start()
        logger.info("Recording started: %s", output_path)
        return self.get_status()

    def stop(self) -> dict[str, Any]:
        if self._recorder is None or not self._recorder.is_active:
            raise RecordingNotActiveError("No active recording")

        output_path = self._recorder.stop()
        frame_count = self._recorder.frame_count
        self._recorder = None

        if frame_count == 0 or not output_path.exists():
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            raise RecordingError("No frames were recorded")

        from video_service.transcoder import transcode_mp4_for_browser

        transcode_mp4_for_browser(output_path)

        logger.info("Recording saved: %s", output_path)
        return {
            "status": "idle",
            "filename": output_path.name,
            "filepath": str(output_path),
            "frameCount": frame_count,
        }

    def stop_if_active(self) -> dict[str, Any] | None:
        if self._recorder is None or not self._recorder.is_active:
            return None
        try:
            return self.stop()
        except RecordingError:
            self._recorder = None
            self._started_at = None
            self._filename = None
            return None

    def get_status(self) -> dict[str, Any]:
        if self._recorder is not None and self._recorder.is_active:
            return {
                "status": "recording",
                "filename": self._filename,
                "startedAt": self._started_at,
                "frameCount": self._recorder.frame_count,
            }
        return {"status": "idle"}
