"""Settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.backend.api.deps import get_app_container
from app.backend.core.container import AppContainer
from app.backend.schemas.camera import (
    MessageResponse,
    PickDirectoryRequest,
    PickDirectoryResponse,
    SavePathRequest,
    SettingsResponse,
)
from platform_utils import pick_directory

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings(
    container: AppContainer = Depends(get_app_container),
) -> SettingsResponse:
    data = container.settings_service.get_all()
    return SettingsResponse(**data)


@router.post("/pick-directory", response_model=PickDirectoryResponse)
def pick_save_directory(body: PickDirectoryRequest) -> PickDirectoryResponse:
    selected = pick_directory(body.initialPath)
    return PickDirectoryResponse(path=selected)


@router.put("/save-path", response_model=MessageResponse)
def update_save_path(
    body: SavePathRequest,
    container: AppContainer = Depends(get_app_container),
) -> MessageResponse:
    container.settings_service.update_save_path(body.path)
    container.ws_manager.schedule_broadcast("settings.save_path", {"path": body.path})
    return MessageResponse(message="save path updated")


@router.put("/record-save-path", response_model=MessageResponse)
def update_record_save_path(
    body: SavePathRequest,
    container: AppContainer = Depends(get_app_container),
) -> MessageResponse:
    container.settings_service.update_record_save_path(body.path)
    container.ws_manager.schedule_broadcast(
        "settings.record_save_path",
        {"path": body.path},
    )
    return MessageResponse(message="record save path updated")
