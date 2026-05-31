"""Camera endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.backend.api.deps import get_app_container
from app.backend.core.container import AppContainer
from app.backend.schemas.camera import CameraInfo
from sdk_adapter.exceptions import CameraNotFoundError

router = APIRouter(prefix="/camera", tags=["camera"])


@router.get("/info", response_model=CameraInfo)
def get_camera_info(container: AppContainer = Depends(get_app_container)) -> CameraInfo:
    try:
        return container.camera_service.get_camera_info()
    except CameraNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
