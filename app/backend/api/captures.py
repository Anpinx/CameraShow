"""Capture endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.backend.api.deps import get_app_container
from app.backend.core.container import AppContainer
from app.backend.schemas.camera import CaptureItem, MessageResponse, SaveCaptureRequest
from sdk_adapter.exceptions import CaptureError, StreamNotRunningError

router = APIRouter(tags=["captures"])


@router.post("/capture", response_model=CaptureItem)
def capture_photo(container: AppContainer = Depends(get_app_container)) -> CaptureItem:
    try:
        jpeg_bytes = container.camera_service.capture_jpeg()
        item = container.capture_service.add_capture(jpeg_bytes)
        container.ws_manager.schedule_broadcast("capture.created", item.model_dump())
        return item
    except StreamNotRunningError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except CaptureError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/captures", response_model=list[CaptureItem])
def list_captures(container: AppContainer = Depends(get_app_container)) -> list[CaptureItem]:
    return container.capture_service.list_captures()


@router.post("/captures/save", response_model=MessageResponse)
def save_capture(
    body: SaveCaptureRequest,
    container: AppContainer = Depends(get_app_container),
) -> MessageResponse:
    try:
        destination = container.capture_service.save_capture_to_path(body.captureId, body.path)
        container.ws_manager.schedule_broadcast(
            "capture.saved",
            {"captureId": body.captureId, "path": str(destination)},
        )
        return MessageResponse(message=f"saved to {destination}")
    except CaptureError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


media_router = APIRouter(prefix="/media/captures", tags=["media"])


@media_router.get("/{capture_id}/full")
def get_capture_image(
    capture_id: str,
    container: AppContainer = Depends(get_app_container),
) -> FileResponse:
    path = container.capture_service.get_image_path(capture_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Capture not found")
    return FileResponse(path, media_type="image/jpeg", filename=path.name)


@media_router.get("/{capture_id}/thumbnail")
def get_capture_thumbnail(
    capture_id: str,
    container: AppContainer = Depends(get_app_container),
) -> FileResponse:
    path = container.capture_service.get_thumbnail_path(capture_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(path, media_type="image/jpeg", filename=path.name)
