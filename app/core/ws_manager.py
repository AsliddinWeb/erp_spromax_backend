import asyncio
from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        conns = self._connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: str, data: dict):
        conns = self._connections.get(str(user_id), [])
        dead = []
        for ws in conns:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, str(user_id))

    def push_to_user(self, user_id: str, data: dict):
        """Sync servis metodlaridan chaqirish uchun — event loop ga task qo'shadi"""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.send_to_user(str(user_id), data))
        except RuntimeError:
            pass


manager = ConnectionManager()
