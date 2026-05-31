"""Video recording endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.backend.api.deps import get_app_container
from app.backend.core.container import AppContainer
from app.backend.schemas.camera import RecordStatusResponse, RecordStopResponse
from sdk_adapter.exceptions import (
    RecordingAlreadyActiveError,
    RecordingError,
    RecordingNotActiveError,
    StreamNotRunningError,
)

router = APIRouter(prefix="/record", tags=["record"])


def _broadcast_record_status(container: AppContainer) -> None:
    status = container.record_service.get_status()
    container.ws_manager.schedule_broadcast("record.status", status)


@router.post("/start", response_model=RecordStatusResponse)
def start_recording(
    container: AppContainer = Depends(get_app_container),
) -> RecordStatusResponse:
    try:
        result = container.record_service.start(container.camera_service.stream_manager)
        _broadcast_record_status(container)
        return RecordStatusResponse(**result)
    except StreamNotRunningError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RecordingAlreadyActiveError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/stop", response_model=RecordStopResponse)
def stop_recording(
    container: AppContainer = Depends(get_app_container),
) -> RecordStopResponse:
    try:
        result = container.record_service.stop()
        record_item = container.record_catalog_service.add_record(
            result["filepath"],
            result["frameCount"],
        )
        container.ws_manager.schedule_broadcast("record.status", {"status": "idle"})
        container.ws_manager.schedule_broadcast("record.stopped", result)
        container.ws_manager.schedule_broadcast("record.created", record_item.model_dump())
        return RecordStopResponse(**result)
    except RecordingNotActiveError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RecordingError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/status", response_model=RecordStatusResponse)
def record_status(
    container: AppContainer = Depends(get_app_container),
) -> RecordStatusResponse:
    return RecordStatusResponse(**container.record_service.get_status())
