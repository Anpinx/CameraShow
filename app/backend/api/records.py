"""Recording catalog endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.backend.api.deps import get_app_container
from app.backend.core.container import AppContainer
from app.backend.schemas.camera import MessageResponse, RecordItem, SaveRecordRequest
from sdk_adapter.exceptions import RecordingError

router = APIRouter(tags=["records"])


@router.get("/records", response_model=list[RecordItem])
def list_records(container: AppContainer = Depends(get_app_container)) -> list[RecordItem]:
    return container.record_catalog_service.list_records()


@router.post("/records/save", response_model=MessageResponse)
def save_record(
    body: SaveRecordRequest,
    container: AppContainer = Depends(get_app_container),
) -> MessageResponse:
    try:
        destination = container.record_catalog_service.save_record_to_path(
            body.recordId,
            body.path,
        )
        container.ws_manager.schedule_broadcast(
            "record.saved",
            {"recordId": body.recordId, "path": str(destination)},
        )
        return MessageResponse(message=f"saved to {destination}")
    except RecordingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


media_router = APIRouter(prefix="/media/records", tags=["media"])


@media_router.get("/{record_id}/full")
def get_record_video(
    record_id: str,
    container: AppContainer = Depends(get_app_container),
) -> FileResponse:
    path = container.record_catalog_service.get_video_path(record_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Recording not found")
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=path.name,
        headers={"Accept-Ranges": "bytes"},
    )


@media_router.get("/{record_id}/thumbnail")
def get_record_thumbnail(
    record_id: str,
    container: AppContainer = Depends(get_app_container),
) -> FileResponse:
    path = container.record_catalog_service.get_thumbnail_path(record_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(path, media_type="image/jpeg", filename=path.name)
