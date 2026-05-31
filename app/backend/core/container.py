"""Application state and dependency container."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.backend.core.websocket_manager import WebSocketManager
from app.backend.services.camera_service import CameraService
from app.backend.services.capture_service import CaptureService
from app.backend.services.record_catalog_service import RecordCatalogService
from app.backend.services.record_service import RecordService
from app.backend.services.settings_service import SettingsService
from third_tools.tool_runner import ToolRunner


@dataclass
class AppContainer:
    camera_service: CameraService
    capture_service: CaptureService
    record_catalog_service: RecordCatalogService
    record_service: RecordService
    settings_service: SettingsService
    tool_runner: ToolRunner
    ws_manager: WebSocketManager = field(default_factory=WebSocketManager)


_container: AppContainer | None = None


def set_container(container: AppContainer) -> None:
    global _container
    _container = container


def get_container() -> AppContainer:
    if _container is None:
        raise RuntimeError("Application container is not initialized")
    return _container
