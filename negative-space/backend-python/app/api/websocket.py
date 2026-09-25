"""WebSocket hub for live Detection, Agent Status, Silence, and Incident
updates pushed to the Observatory UI."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self.active.append(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            if ws in self.active:
                self.active.remove(ws)

    async def broadcast(self, message: dict):
        payload = json.dumps(message, default=str)
        async with self._lock:
            dead = []
            for ws in self.active:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active.remove(ws)


manager = ConnectionManager()


@router.websocket("/ws/live")
async def live_updates(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # The client doesn't need to send anything; this just keeps
            # the socket alive and lets us detect disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
