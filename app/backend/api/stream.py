"""Stream endpoints."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.backend.api.deps import get_app_container
from app.backend.core.config import get_video_config
from app.backend.core.container import AppContainer
from app.backend.schemas.camera import StreamCloseResponse, StreamOpenResponse, StreamStatusResponse
from sdk_adapter.exceptions import CameraNotFoundError, SDKError

router = APIRouter(prefix="/stream", tags=["stream"])


@router.post("/open", response_model=StreamOpenResponse)
def open_stream(container: AppContainer = Depends(get_app_container)) -> StreamOpenResponse:
    try:
        return container.camera_service.open_stream()
    except CameraNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (SDKError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/close", response_model=StreamCloseResponse)
def close_stream(container: AppContainer = Depends(get_app_container)) -> StreamCloseResponse:
    stopped = container.record_service.stop_if_active()
    if stopped:
        record_item = container.record_catalog_service.add_record(
            stopped["filepath"],
            stopped["frameCount"],
        )
        container.ws_manager.schedule_broadcast("record.stopped", stopped)
        container.ws_manager.schedule_broadcast("record.created", record_item.model_dump())
    container.ws_manager.schedule_broadcast(
        "record.status",
        container.record_service.get_status(),
    )
    return container.camera_service.close_stream()


@router.get("/status", response_model=StreamStatusResponse)
def stream_status(container: AppContainer = Depends(get_app_container)) -> StreamStatusResponse:
    return container.camera_service.get_stream_status()


def _mjpeg_boundary() -> str:
    return "frame"


@router.get("/mjpeg")
async def mjpeg_stream(container: AppContainer = Depends(get_app_container)) -> StreamingResponse:
    manager = container.camera_service.stream_manager
    if not manager.is_running:
        raise HTTPException(status_code=409, detail="Stream is offline")

    video_cfg = get_video_config().get("video", {})
    fps = int(video_cfg.get("mjpeg_fps", 15))
    boundary = _mjpeg_boundary()
    frame_buffer = manager.frame_buffer

    async def event_generator():
        interval = 1.0 / max(fps, 1)
        last_frame: bytes | None = None
        while manager.is_running:
            frame = frame_buffer.get_latest()
            if frame and frame is not last_frame:
                last_frame = frame
                chunk = (
                    f"--{boundary}\r\n"
                    "Content-Type: image/jpeg\r\n"
                    f"Content-Length: {len(frame)}\r\n\r\n"
                ).encode("ascii") + frame + b"\r\n"
                yield chunk
            await asyncio.sleep(interval)

    return StreamingResponse(
        event_generator(),
        media_type=f"multipart/x-mixed-replace; boundary={boundary}",
    )
