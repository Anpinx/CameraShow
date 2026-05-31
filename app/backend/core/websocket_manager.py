"""WebSocket connection manager for status push."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._loop = asyncio.get_running_loop()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("WebSocket client connected, total=%s", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("WebSocket client disconnected, total=%s", len(self._connections))

    async def broadcast(self, event: str, payload: dict[str, Any]) -> None:
        message = json.dumps({"event": event, "data": payload}, ensure_ascii=False)
        stale: list[WebSocket] = []
        async with self._lock:
            connections = list(self._connections)
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception:  # noqa: BLE001
                stale.append(connection)
        if stale:
            async with self._lock:
                for connection in stale:
                    self._connections.discard(connection)

    def schedule_broadcast(self, event: str, payload: dict[str, Any]) -> None:
        loop = self._loop
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning("Cannot broadcast %s: event loop not available", event)
                return

        if loop.is_running():
            loop.create_task(self.broadcast(event, payload))
        else:
            asyncio.run_coroutine_threadsafe(self.broadcast(event, payload), loop)
