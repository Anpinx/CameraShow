"""FastAPI application entrypoint."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.backend.api.router import api_router
from app.backend.core.config import get_app_config, get_tools_config, resolve_path
from app.backend.core.container import AppContainer, set_container
from app.backend.core.logging_config import configure_logging, get_logger
from app.backend.core.websocket_manager import WebSocketManager
from app.backend.services.camera_service import CameraService
from app.backend.services.capture_service import CaptureService
from app.backend.services.record_catalog_service import RecordCatalogService
from app.backend.services.record_service import RecordService
from app.backend.services.settings_service import SettingsService
from third_tools.tool_runner import ToolRunner

logger = get_logger(__name__)


def _ensure_data_dirs() -> None:
    app_cfg = get_app_config()
    paths_cfg = app_cfg.get("paths", {})
    for key in ("captures", "records", "temp"):
        relative = str(paths_cfg.get(key, f"data/{key}"))
        resolve_path(relative)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    _ensure_data_dirs()

    ws_manager = WebSocketManager()
    ws_manager.bind_loop(asyncio.get_running_loop())
    camera_service = CameraService(ws_manager)
    camera_service.initialize()

    settings_service = SettingsService()
    container = AppContainer(
        camera_service=camera_service,
        capture_service=CaptureService(),
        record_catalog_service=RecordCatalogService(),
        record_service=RecordService(settings_service),
        settings_service=settings_service,
        tool_runner=ToolRunner(get_tools_config().get("tools", {})),
        ws_manager=ws_manager,
    )
    set_container(container)

    app_cfg = get_app_config().get("app", {})
    logger.info(
        "CameraDemo backend started on %s:%s",
        app_cfg.get("host", "127.0.0.1"),
        app_cfg.get("port", 8000),
    )
    try:
        yield
    finally:
        container.camera_service.shutdown()
        logger.info("CameraDemo backend stopped")


def create_app() -> FastAPI:
    app_cfg = get_app_config().get("app", {})
    app = FastAPI(
        title=str(app_cfg.get("name", "CameraDemo")),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    cors_cfg = get_app_config().get("cors", {})
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_cfg.get("allow_origins", ["*"]),
        allow_credentials=bool(cors_cfg.get("allow_credentials", True)),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_app_config().get("app", {})
    uvicorn.run(
        "app.backend.main:app",
        host=str(settings.get("host", "127.0.0.1")),
        port=int(settings.get("port", 8000)),
        reload=bool(settings.get("debug", False)),
    )
