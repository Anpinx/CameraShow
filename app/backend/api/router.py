"""API router aggregation."""

from __future__ import annotations

from fastapi import APIRouter

from app.backend.api import camera, captures, record, records, settings, stream, websocket

api_router = APIRouter(prefix="/api")
api_router.include_router(camera.router)
api_router.include_router(stream.router)
api_router.include_router(captures.router)
api_router.include_router(captures.media_router)
api_router.include_router(record.router)
api_router.include_router(records.router)
api_router.include_router(records.media_router)
api_router.include_router(settings.router)
api_router.include_router(websocket.router)
