"""WebSocket status channel."""

from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.backend.api.deps import get_app_container
from app.backend.core.container import AppContainer

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/status")
async def websocket_status(
    websocket: WebSocket,
    container: AppContainer = Depends(get_app_container),
) -> None:
    await container.ws_manager.connect(websocket)
    try:
        status = container.camera_service.get_stream_status()
        await websocket.send_json(
            {
                "event": "stream.status",
                "data": status.model_dump(exclude_none=True),
            }
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await container.ws_manager.disconnect(websocket)
